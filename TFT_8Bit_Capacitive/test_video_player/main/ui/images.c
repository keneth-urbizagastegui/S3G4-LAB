#include "images.h"

const ext_img_desc_t images[8] = {
    { "rew10", &img_rew10 },
    { "fwd10", &img_fwd10 },
    { "lock", &img_lock },
    { "queue", &img_queue },
    { "sdcard", &img_sdcard },
    { "sdcard_big", &img_sdcard_big },
    { "sdcard_error_big", &img_sdcard_error_big },
    { "film", &img_film },
};