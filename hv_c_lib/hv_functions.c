// hv_functions.c

#include "hv_functions.h"

int log_in(char* ip_address, char* username, char* password) {
    int sys_handle = -1;
    CAENHVRESULT ret;
    int sys_type = 3;
    int link = LINKTYPE_TCPIP;
    //char arg[30] = "192.168.10.81";
    //char user_name[30] = "admin";
    //char passwd[30] = "admin";
    ret = CAENHV_InitSystem((CAENHV_SYSTEM_TYPE_t)sys_type, link, ip_address, username, password, &sys_handle);
    if (ret == CAENHV_OK) {
        printf("Start good\n");
    }
    else {
        printf("Start bad\n");
    }

	printf("System handle is: %d\n", sys_handle);
	get_crate_map(sys_handle);

    return sys_handle;
}


void get_crate_map(int sys_handle) {
	unsigned short NrOfSl, * SerNumList, * NrOfCh;
	char* ModelList, * DescriptionList;
	unsigned char* FmwRelMinList, * FmwRelMaxList;
	CAENHVRESULT ret = CAENHV_GetCrateMap(sys_handle, &NrOfSl, &NrOfCh, &ModelList, &DescriptionList, &SerNumList,
		&FmwRelMinList, &FmwRelMaxList);

    if (ret == CAENHV_OK) {
		printf("Crate Map good\n");
		printf("Number of slots: %d\n", NrOfSl);
		for (int i = 0; i < NrOfSl; i++) {
			printf("Slot %d\n", i);
			printf("Model: %s\n", ModelList + i * 16);
			printf("Description: %s\n", DescriptionList + i * 16);
			printf("Serial number: %d\n", SerNumList[i]);
			printf("Firmware min: %d\n", FmwRelMinList[i]);
			printf("Firmware max: %d\n", FmwRelMaxList[i]);
			printf("Number of channels: %d\n", NrOfCh[i]);
		}
	}
    else {
		printf("Crate Map bad\n");
    }
}


void log_out(int sys_handle) {
	CAENHVRESULT ret = CAENHV_DeinitSystem(sys_handle);
	if (ret == CAENHV_OK) {
		printf("Shut down good\n");
	}
	else {
		printf("Shut down bad\n");
	}
}


int get_ch_power(int sys_handle, int slot, int chan) {
	unsigned short ch_list[] = { chan };
	unsigned short ch_status[1];
	CAENHVRESULT ret = CAENHV_GetChParam(sys_handle, slot, "Pw", 1, ch_list, ch_status);
	if (ret == CAENHV_OK) {
		printf("Power read good\n");
	}
	else {
		printf("Power read bad\n");
	}
	return ch_status[0];
}


float get_ch_vmon(int sys_handle, int slot, int chan) {
	unsigned short ch_list[] = { chan };
	float ch_status[1];
	CAENHVRESULT ret = CAENHV_GetChParam(sys_handle, slot, "VMon", 1, ch_list, ch_status);
	if (ret == CAENHV_OK) {
		printf("Voltage read good\n");
	}
	else {
		printf("Voltage read bad\n");
	}
	return ch_status[0];
}


void set_ch_v0(int sys_handle, int slot, int chan, float value) {
	unsigned short ch_list[] = { chan };
	unsigned short ch_value[] = { value };
	CAENHVRESULT ret = CAENHV_SetChParam(sys_handle, slot, "V0Set", 1, ch_list, ch_value);
	if (ret == CAENHV_OK) {
		printf("Voltage set good\n");
	}
	else {
		printf("Voltage set bad\n");
	}
}


void set_ch_pw(int sys_handle, int slot, int chan, int value) {
	unsigned short ch_list[] = { chan };
	unsigned short ch_value[] = { value };
	CAENHVRESULT ret = CAENHV_SetChParam(sys_handle, slot, "Pw", 1, ch_list, ch_value);
	if (ret == CAENHV_OK) {
		printf("Power set good\n");
	}
	else {
		printf("Power set bad\n");
	}
}