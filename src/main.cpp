#include "bn_core.h"
#include "bn_keypad.h"
#include "bn_log.h"
#include "bn_sprite_builder.h"
#include "bn_sprite_ptr.h"

#include "level.h"
#include "debug.h"
#include "player.h"
#include "generated/levels_intgrid.h"
#include "generated/world_config.h"

int main()
{
    bn::core::init();

    bn::camera_ptr camera = bn::camera_ptr::create(0, 0);

    cd::Level *current_level = cd::levels[0];
    cd::Player player = cd::Player(camera);

    current_level->init(camera);

    cd::log("Start Game!");

    while (true)
    {
        current_level->tick(camera);
        player.on_tick(current_level);

        bn::core::update();
    }
}
