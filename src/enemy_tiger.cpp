#include "enemy_tiger.h"

using namespace cd;

EnemyTiger::EnemyTiger(
    bn::fixed _id, bn::camera_ptr _camera, bn::fixed_point _position, bn::fixed_point **_steps, bn::fixed _steps_number) : Enemy(_id, _camera, _position, _steps, _steps_number)
{
    sprite = bn::sprite_items::tiger.create_sprite(0, 0);

    sprite.value().set_position(from);
    sprite.value().set_camera(camera);
    sprite.value().set_visible(true);
}

EnemyTiger::~EnemyTiger()
{
}

void EnemyTiger::set_animation_right_walk()
{
    if (animation.has_value() && animation.value().graphics_indexes().front() == 0)
    {
        return;
    }
    sprite.value().set_horizontal_flip(false);
    animation = bn::create_sprite_animate_action_forever(
        sprite.value(),
        8,
        bn::sprite_items::tiger.tiles_item(),
        0, 1, 2, 3, 4, 5, 6, 7);
}

void EnemyTiger::set_animation_left_walk()
{
    set_animation_right_walk();
    sprite.value()
        .set_horizontal_flip(true);
}

void EnemyTiger::set_animation_down_walk()
{
    if (animation.has_value() && animation.value().graphics_indexes().front() == 16)
    {
        return;
    }
    animation = bn::create_sprite_animate_action_forever(
        sprite.value(),
        8,
        bn::sprite_items::tiger.tiles_item(),
        16, 17, 18, 19, 20, 21, 22, 23);
}

void EnemyTiger::set_animation_up_walk()
{
    if (animation.has_value() && animation.value().graphics_indexes().front() == 32)
    {
        return;
    }
    animation = bn::create_sprite_animate_action_forever(
        sprite.value(),
        8,
        bn::sprite_items::tiger.tiles_item(),
        32, 33, 34, 35, 36, 37, 38, 39);
}