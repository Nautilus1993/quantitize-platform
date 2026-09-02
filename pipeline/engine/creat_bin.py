
import sys
import os

# 清理 sys.path，移除 Isaac Sim 等可能冲突的路径
# 这必须在导入 numba 之前完成
sys.path = [p for p in sys.path if p and 'isaac-sim' not in p.lower()]

import struct
import numpy as np
import random
import numba as nb
from numba import jit

#################### hardware defines ##########################
base_Tin                    =32
Tout                        =32

Tin                         =base_Tin
Tb                          =1

def parallel_of_feature(input, CH, H, W):
    slice_of_CH = (CH + Tout - 1) // Tout
    output = np.zeros((slice_of_CH, H, W, Tout))
    for h in range(H):
        for w in range(W):
            for ch in range(slice_of_CH):
                for t in range(Tout):
                    if ch * Tout + t < CH:
                        tp = input[ch * Tout + t][h][w]
                    else:
                        tp = 0
                    output[ch][h][w][t] = tp
    return output

def parallel_of_bn(bn_input, CH):
    slice_of_CH = (CH + Tout - 1) // Tout
    Total_CH = slice_of_CH*Tout*2
    bn_output = np.zeros((Total_CH))
    for chout in range(CH):
        for i in range(2):
            bn_output[2*chout+i] = bn_input[chout][i]
    return bn_output.flatten()


def parallel_weight(weight_input, CHout, CHin, Ky, Kx):
    slice_of_CHin = (CHin + Tin - 1) // Tin
    slice_of_CHout = (CHout + Tout - 1) // Tout
    weight_reorg = np.zeros((slice_of_CHout, slice_of_CHin, Ky, Kx, Tout, Tin))
    for chout in range(slice_of_CHout):
        for chin in range(slice_of_CHin):
            for ky in range(Ky):
                for kx in range(Kx):
                    for tout in range(Tout):
                        for tin in range(Tin):
                            if chout * Tout + tout < CHout and chin * Tin + tin < CHin:
                                tp1 = weight_input[chout * Tout + tout][chin * Tin + tin][ky][kx]
                                # print(chout, chin, ky, kx, tout, ll, tout)
                            else:
                                tp1 = 0
                            weight_reorg[chout][chin][ky][kx][tout][tin] = tp1
    return weight_reorg


# @jit(nopython=True)
def fp16int_mul_conv_bn(conv_input, conv_weight, bn_wt_and_bias, conv_output, Ky, Kx, Sy, Sx, Py, Px):

    CHin = conv_input.shape[0]
    Hin = conv_input.shape[1]
    Win = conv_input.shape[2]
    CHout = conv_output.shape[0]
    Hout = conv_output.shape[1]
    Wout = conv_output.shape[2]

    for chout in range(CHout):
        for hout in range(Hout):
            for wout in range(Wout):
                tp_sum = 0
                for chin in range(CHin):
                    for ky in range(Ky):
                        for kx in range(Kx):
                            hin = hout*Sy - Py + ky
                            win = wout*Sx - Px + kx
                            if not (hin < 0 or win < 0 or hin >= Hin or win >= Win):
                                dat = conv_input[chin][hin][win]
                            else:
                                dat = 0
                            wt = conv_weight[chout][chin][ky][kx]
                            tp_sum += dat * wt

                conv_output[chout][hout][wout] = tp_sum * bn_wt_and_bias[2*chout+1] + bn_wt_and_bias[2*chout+0]
                # print("output[ch%d][h%d][w%d]=%10f" %(chout, hout, wout, conv_output[chout][hout][wout]))
    return conv_output


def fp16array_to_bin(input_array, output_file):
    float_array = np.array(input_array, dtype=np.float32) # 转换为numpy数组
    fp16_array = float_array.astype(np.float16)          # 转换为FP16格式
    fp16_array.tofile(output_file)                       # 保存为二进制文件


def INTarray_to_bin(dat_in, bin_out):
    count=len(dat_in)
    # print(count)
    mod = count%2
    if (mod):
        dat_out_0 = np.zeros((count + 2 - mod) // 2)
    else:
        dat_out_0 = np.zeros(count // 2)

    if(mod):
        print("txt行数不是2的倍数，补充", (2-mod),"行0")
        for i in range(2-mod):
            dat_in = np.append(dat_in,0)
        #print(dat_in)

    for i in range(dat_out_0.size):
        a1 = int(dat_in[2 * i])
        if (a1 < 0):
            a1 = 256 + a1
        a1 = a1

        a2 = int(dat_in[2 * i + 1])
        if (a2 < 0):
            a2 = 256 + a2
        a2 = a2 * 256

        b = a1 + a2
        if ((b <= 32767 )& (b >= -32768)):
            b=b
        else:
            b = b - 65536
        dat_out_0[i] = b

    dat_out_1 = open(bin_out, 'wb')
    size = dat_out_0.size
    for i in range(size):
        a = int(dat_out_0[i])
        b = struct.pack('h', a)
        dat_out_1.write(b)
    dat_out_1.close()


def creat_bin(data_in, output_name):
    if 'wt' in output_name:
        CHout, CHin, Ky, Kx = data_in.shape
        Tdata = parallel_weight    (data_in, CHout, CHin, Ky, Kx)
    elif 'bn' in output_name:
        CHout,_ = data_in.shape
        Tdata     = parallel_of_bn     (data_in, CHout)
    else:
        CHin,CHout,Hout,Wout = data_in.shape
        if CHin == 1:
            data_in = data_in.reshape((CHout,Hout,Wout))
        if CHout == 1:
            data_in = data_in.reshape((CHin,Hout,Wout))
    
        Tdata = parallel_of_feature(data_in, CHout,Hout,Wout)

        
    
    output_name = output_name.replace('txt', 'bin')
    output_name = os.path.join(os.path.dirname(output_name), output_name.split('/')[-1].replace('T32', 'T32_T32'))
    if 'wt.bin' in output_name:
        print(output_name, '   int8')
        INTarray_to_bin  (Tdata.flatten(), output_name) 
    else:
        print(output_name, '   fl')
        fp16array_to_bin (Tdata.flatten(), output_name)
    