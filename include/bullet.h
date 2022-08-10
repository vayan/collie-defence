#ifndef COLLIE_DEFENCE_GBA_BULLET_H
#define COLLIE_DEFENCE_GBA_BULLET_H

#include "bn_regular_bg_ptr.h"
#include "bn_regular_bg_item.h"
#include "bn_fixed.h"
#include "bn_optional.h"
#include "bn_core.h"
#include "bn_fixed_point.h"
#include "bn_camera_ptr.h"
#include "bn_vector.h"
#include "bn_memory.h"
#include "bn_format.h"
#include "bn_vector.h"
#include "bn_log.h"
#include "bn_math.h"
#include "bn_size.h"
#include "bn_unique_ptr.h"
#include "bn_sprite_builder.h"
#include "bn_sprite_ptr.h"
#include "bn_timer.h"

#include "bn_sprite_items_bullet.h"

#include "math.h"
#include "target.h"
#include "debug.h"

namespace cd
{
    class Bullet
    {
    public:
        Bullet(
            bn::camera_ptr camera,
            bn::fixed_point position,
            Target *target);

        ~Bullet();

        void on_tick();

        bool to_be_destroyed();

    private:
        bn::fixed_point position;
        bn::camera_ptr camera;
        Target *target;
        bn::optional<bn::sprite_ptr>
            sprite;
        bool destroyed = false;
        bn::fixed progress = 0;
        bn::fixed delta = 0.01;
    };
}

#endif