#include <stdio.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <termios.h>
#include <unistd.h>
#include "CAENHVWrapper.h"
#include <fcntl.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
//#include "console.h"


void main() {
    int sys_handle=-1;
    CAENHVRESULT ret;
    int sys_type = 3;
    int link = LINKTYPE_TCPIP;
    char arg[30] = "192.168.10.81";
    char user_name[30] = "admin";
    char passwd[30] = "admin";
    ret = CAENHV_InitSystem((CAENHV_SYSTEM_TYPE_t)sys_type, link, arg, user_name, passwd, &sys_handle);
    if (ret == CAENHV_OK) {
        printf("Start good\n");
    } else {
        printf("Start bad\n");
    }
    printf("Here\n");
    printf("System handle is: %d\n", sys_handle);
    printf("System id is: %d\n", ret);

    unsigned short NrOfSl, *SerNumList, *NrOfCh;
    char *ModelList, *DescriptionList;
    unsigned char *FmwRelMinList, *FmwRelMaxList;
    ret = CAENHV_GetCrateMap(handle, &NrOfSl, &NrOfCh, &ModelList, &DescriptionList, &SerNumList,
        &FmwRelMinList, &FmwRelMaxList);
    if (ret == CAENHV_OK) {
        printf("Crate Map good\n");
    }
    else {
        printf("Crate Map bad\n");
    }

    const unsigned short ch_list[] = {2};
    const char ch_name[] = {"test1343"};
    ret = CAENHV_SetChName(sys_handle, 0, 1, ch_list, ch_name);
    if (ret == CAENHV_OK) {
        printf("Rename good\n");
    } else {
        printf("Rename bad\n");
        printf("Error: %s\n", CAENHV_GetError(sys_handle));
    }

    ret = CAENHV_DeinitSystem(sys_handle);
    if (ret == CAENHV_OK) {
        printf("Shut down good\n");
    } else {
        printf("Shut down bad\n");
        printf("Error: %s\n", CAENHV_GetError(sys_handle));
    }
}
