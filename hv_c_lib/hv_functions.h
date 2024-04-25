// hv_functions.h

#ifndef HV_FUNCTIONS_H
#define HV_FUNCTIONS_H

#include <stdio.h>
#include "CAENHVWrapper.h"

int log_in(char* ip_address, char* username, char* password);
void get_crate_map(int sys_handle);
void log_out(int sys_handle);

int get_ch_power(int sys_handle, int slot, int chan);

float get_ch_vmon(int sys_handle, int slot, int chan);
void set_ch_v0(int sys_handle, int slot, int chan, int value);


#endif