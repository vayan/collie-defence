#include "cursor.h"
#include "game.h"
#include "player.h"

using namespace cd;

Cursor::Cursor(bn::camera_ptr _camera) : camera(_camera)
{
    bn::blending::set_transparency_alpha(0.4); // for the tower preview

    sprite = bn::sprite_items::cursor.create_sprite(0, 0);

    position = bn::fixed_point(0, 0);
    sprite.value().set_camera(_camera);
    sprite.value()
        .set_position(position);
}

Cursor::~Cursor()
{
}

void Cursor::enable()
{
    targeting_buildable_grid = true;
    sprite.value().set_item(bn::sprite_items::cursor, 0);
}

void Cursor::disable()
{
    targeting_buildable_grid = false;
    sprite.value()
        .set_item(bn::sprite_items::cursor, 1);
}

bool Cursor::can_build(Level *level)
{
    GridTileType top_left_grid = level->get_map_cell(
        position.x() - 8,
        position.y() - 8);
    GridTileType bottom_right_grid = level->get_map_cell(
        position.x() + 7,
        position.y() + 7);
    // TODO check other corners

    for (Tower *tower : *level->get_towers())
    {
        if (tower->get_hitbox().intersects(get_hitbox()))
        {
            return false;
        }
    }

    if (top_left_grid == bottom_right_grid && top_left_grid == GridTileType::buildable)
    {
        return true;
    }

    return false;
}

void Cursor::on_tick(Game *game)
{
    if (can_build(game->get_current_level()))
    {
        enable();
    }
    else
    {
        disable();
    }

    if (
        bn::keypad::a_pressed() &&
        targeting_buildable_grid &&
        current_selection.has_value())
    {
        bn::fixed cost = current_selection.value()->get_cost();

        if (game->get_player()->get_money() >= cost)
        {
            bool success = game->get_current_level()->add_tower(current_selection.value());

            if (success)
            {
                game->get_player()->spend_money(cost);
            }
            remove_current_selection(!success);
        }
        else
        {
            // TODO show no money warning
        }
    }

    if (shop.has_value())
    {
        shop.value().on_tick(game);

        if (shop.value().get_purchase().has_value())
        {
            set_selection(shop.value().get_purchase().value());
        }
        if (shop.has_value() && shop.value().is_closed())
        {
            hide_shop();
        }
    }
    else
    {
        if (bn::keypad::b_pressed())
        {
            show_shop();
        }

        if (bn::keypad::right_pressed())
        {
            position.set_x(position.x() + 8);
        }

        if (bn::keypad::left_pressed())
        {
            position.set_x(position.x() - 8);
        }

        if (bn::keypad::down_pressed())
        {
            position.set_y(position.y() + 8);
        }

        if (bn::keypad::up_pressed())
        {
            position.set_y(position.y() - 8);
        }
    }

    if (current_selection.has_value())
    {
        current_selection.value()->set_position(position.x(), position.y());
    }

    if (range.has_value())
    {
        range.value().set_position(position);
    }

    check_screen_bounds();

    // can re-enable this if I do levels bigger than 240×160
    // update_camera(level->get_bg().value());
    sprite.value()
        .set_position(position);
}

void Cursor::update_camera(bn::regular_bg_ptr map)
{
    bn::fixed x = position.x();
    bn::fixed y = position.y();
    bn::fixed half_map_width = map.dimensions().width() / 2;
    bn::fixed half_map_height = map.dimensions().height() / 2;
    bn::fixed half_display_width = bn::display::width() / 2;
    bn::fixed half_display_height = bn::display::height() / 2;

    bn::fixed min_x = -(half_map_width - half_display_width);
    bn::fixed max_x = half_map_width - half_display_width;
    bn::fixed min_y = -(half_map_height - half_display_height);
    bn::fixed max_y = half_map_height - half_display_height;

    if (x < min_x)
    {
        x = min_x;
    }
    else if (x > max_x)
    {
        x = max_x;
    }
    else
    {
        x = x;
    }

    if (y < min_y)
    {
        y = min_y;
    }
    else if (y > max_y)
    {
        y = max_y;
    }
    else
    {
        y = y;
    }

    camera.set_position(x, y);
}

bn::fixed_rect Cursor::get_hitbox()
{
    return bn::fixed_rect(
        position.x(),
        position.y(),
        sprite.value().dimensions().width(),
        sprite.value().dimensions().height());
}

void Cursor::remove_current_selection(bool hard_clean)
{
    if (current_selection.has_value() && hard_clean)
    {
        delete current_selection.value();
    }
    current_selection.reset();
    range.reset();
}

void Cursor::hide_shop()
{
    if (shop.has_value())
    {
        shop.reset();
    }
}

void Cursor::show_shop()
{
    remove_current_selection(true);
    shop = Shop(camera);
}

void Cursor::set_selection(TowerType type)
{
    hide_shop();

    switch (type)
    {
    case TowerType::Sticky:
        current_selection = new TowerMagic(camera, position);
        break;
    case TowerType::AoE:
        current_selection = new TowerBallista(camera, position);
        break;
    default:
        current_selection = new TowerBasic(camera, position);
        break;
    }

    // range background is 128x128px
    bn::fixed scale = current_selection.value()->get_aggro_range().safe_division(64);

    range = bn::affine_bg_items::range.create_bg(0, 0);
    range.value().set_camera(camera);
    range.value().set_visible(true);
    range.value().set_wrapping_enabled(false);
    range.value().set_blending_enabled(true);
    range.value().set_priority(0);
    range.value().set_horizontal_scale(scale);
    range.value().set_vertical_scale(scale);
}

void Cursor::check_screen_bounds()
{
    bn::fixed x = position.x();
    bn::fixed y = position.y();
    bn::fixed half_display_width = bn::display::width() / 2;
    bn::fixed half_display_height = bn::display::height() / 2;

    if (x < -half_display_width)
    {
        x = -half_display_width;
    }
    else if (x > half_display_width)
    {
        x = half_display_width;
    }

    if (y < -half_display_height)
    {
        y = -half_display_height;
    }
    else if (y > half_display_height)
    {
        y = half_display_height;
    }

    position.set_x(x);
    position.set_y(y);
}
