import json
import numpy
import os
from PIL import Image

from ldtkpy.api import ldtk_json_from_dict

LTDK_PROJECT_PATH = os.getenv("LDTK_PATH")
BASE_LTDK_PROJECT_PATH = os.path.dirname(LTDK_PROJECT_PATH)

OFFSET_WORLD_MAP = 0  # needs to be multiple of 256 (offset to avoid negative coordinate, easier on 2D arrays)
STRING_METADATA_SIZE = 45

print("\nLoading LTdk JSON..")
content = None
with open(LTDK_PROJECT_PATH) as f:
    content = ldtk_json_from_dict(json.load(f))
print("Done!\n")


def parse_entities(entities):
    print("Parsing entities values...")
    _entities_tiles_values = {}

    for entity in entities:
        _entities_tiles_values.update({entity.identifier: entity.uid})
    print("Done!\n")
    return _entities_tiles_values


# parse grid tiles ID like platform=1, spikes=3 etc...
def parse_grid_tiles_values(layers):
    print("Parsing grid tiles values...")
    _grid_tiles_values = {}

    for layer in layers:
        if layer.type != "IntGrid":
            continue
        for int_grid_value in layer.int_grid_values:
            _grid_tiles_values.update({int_grid_value.identifier: int_grid_value.value})

    print("Done!\n")
    return _grid_tiles_values


def generate_world_file(
    _grid_tiles_values, _entities_tiles_values, _world_int_grid, _levels
):
    print("Generating world header file...")

    tiles_int_def = ""
    for (k, v) in _grid_tiles_values.items():
        tiles_int_def = f"{tiles_int_def}{k} = {v},\n"

    entities_def = ""
    for (k, v) in _entities_tiles_values.items():
        entities_def = f"{entities_def}{k} = {v},\n"

    enums = f"""
    enum class GridTileType {{
         empty = 0,
         {tiles_int_def}
    }};

    enum class EntityType {{
         {entities_def}
    }};
    """

    intgrid_map_filename = f"./include/generated/world_config.h"
    os.makedirs(os.path.dirname(intgrid_map_filename), exist_ok=True)
    with open(intgrid_map_filename, "w") as intgridkey_file:
        intgridkey_file.write(
            f"""
#ifndef COLLIE_DEFENCE_GBA_LEVEL_WORLDCONFIG_H
#define COLLIE_DEFENCE_GBA_LEVEL_WORLDCONFIG_H

namespace cd {{
    {enums}
    static const int world_grid_width = {content.world_grid_width};
    static const int world_grid_height = {content.world_grid_height};
    static const int world_int_grid[] = {str(_world_int_grid).replace('[', '{').replace(']', '}')};
    static const int string_metadata_max_size = {STRING_METADATA_SIZE};
}}

#endif
"""
        )
    print("Done!\n")


def parse_levels(_levels):
    print("Parsing all levels...")
    parsed_levels = []
    for index, raw_level in enumerate(_levels):
        parsed_level = {
            "int_identifier": index,
            "identifier": raw_level.identifier,
            "width": raw_level.px_wid,
            "height": raw_level.px_hei,
            # TODO use this int_grid_width to check for invalid level, if the division doesn't give an int exclude the level
            "int_grid_width": int(raw_level.px_wid / content.world_grid_width),
            "int_grid_height": int(raw_level.px_hei / content.world_grid_height),
            "world_x": raw_level.world_x + OFFSET_WORLD_MAP,
            "world_y": raw_level.world_y + OFFSET_WORLD_MAP,
            "world_int_grid_x": int(
                (raw_level.world_x + OFFSET_WORLD_MAP) / content.world_grid_width
            ),
            "world_int_grid_y": int(
                (raw_level.world_y + OFFSET_WORLD_MAP) / content.world_grid_height
            ),
        }
        for layer_instance in raw_level.layer_instances:
            if (
                layer_instance.type == "IntGrid"
                and layer_instance.identifier == "IntGrid"
            ):
                parsed_level.update({"int_grid": layer_instance.int_grid_csv})
                pass
            if layer_instance.type == "Entities":
                entities = []
                for entity_instance in layer_instance.entity_instances:
                    fields = {"point": [], "str": []}
                    for field_instance in entity_instance.field_instances:
                        if field_instance.type == "Point":
                            fields["point"].append(
                                {field_instance.identifier: field_instance.value}
                            )
                        else:
                            fields["str"].append(
                                {field_instance.identifier: field_instance.value}
                            )
                    entities.append(
                        {
                            "type": entity_instance.identifier,
                            "location": entity_instance.px,
                            "fields": fields,
                        }
                    )
                parsed_level.update({"entities": entities})
                pass
        parsed_levels.append(parsed_level)
    print("Done!\n")
    return parsed_levels


def generate_world_int_grid(_levels):
    print("Generating a world grid int map...")
    world_int_grid = numpy.empty(
        shape=(
            100,
            100,
        ),  # TODO we need to use the 100 size in the code, maybe I should store it in headers
        dtype=int,
    )
    world_int_grid.fill(-1)

    for _level in _levels:
        for col in range(_level["int_grid_width"]):
            for row in range(_level["int_grid_height"]):
                world_col = col + _level["world_int_grid_x"]
                world_row = row + _level["world_int_grid_y"]
                world_int_grid[world_row, world_col] = _level["int_identifier"]
    print("Done!\n")
    return world_int_grid.flatten().tolist()


def generate_level_intgrid_file(_levels):
    intgrid_string = []
    headers = ""
    intgridfilename = f"./include/generated/levels_intgrid.h"
    os.makedirs(os.path.dirname(intgridfilename), exist_ok=True)

    for _level in _levels:
        headers = (
            f'{headers}\n#include "generated/levels/level_{_level["int_identifier"]}.h"'
        )
        intgrid_string.append(f'&level_{_level["int_identifier"]}')

    with open(intgridfilename, "w") as cpp_file:
        cpp_file.write(
            f"""
#ifndef COLLIE_DEFENCE_GBA_LEVEL_INTGRID_H
#define COLLIE_DEFENCE_GBA_LEVEL_INTGRID_H
{headers}
#include "level.h"

namespace cd {{
    BN_DATA_EWRAM static Level* levels[] = {str(intgrid_string).replace('[', '{').replace(']', '}').replace("'", '')};
}}

#endif
"""
        )


def import_level_png(_levels):
    print("Converting all levels PNG to BMP/JSON...")
    for _level in _levels:
        zfill_id = str(_level["int_identifier"]).zfill(4)
        os.makedirs("./graphics/generated/levels", exist_ok=True)

        image_png = f'{BASE_LTDK_PROJECT_PATH}/levels/png/{_level["identifier"]}.png'
        img = Image.open(image_png)
        newimg = img.convert(mode="P")
        newimg.save(f"./graphics/generated/levels/levels_{zfill_id}.bmp")

        json_filename = f"./graphics/generated/levels/levels_{zfill_id}.json"
        with open(json_filename, "w") as json_file:
            json_file.write(
                f"""{{
  "type": "regular_bg"
}}"""
            )
    print("Done!\n")


entities_tiles_values = parse_entities(content.defs.entities)

grid_tiles_values = parse_grid_tiles_values(content.defs.layers)

levels = parse_levels(content.levels)

world_int_grid = generate_world_int_grid(levels)

generate_world_file(grid_tiles_values, entities_tiles_values, world_int_grid, levels)

generate_level_intgrid_file(levels)

import_level_png(levels)

print("Generating all levels header files...")
for level_index, level in enumerate(levels):
    zfill_id = str(level["int_identifier"]).zfill(4)
    level_name = f'level_{level["int_identifier"]}'
    filename = f"./include/generated/levels/{level_name}.h"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    entities_var_list = []
    entities_var_declar = ""

    for index, entity in enumerate(level["entities"]):
        id = level_index * 1000 + index
        points_var_declr = ""
        points_var_list = []
        strings_var_declr = ""
        strings_var_list = []
        var_name = f'level_{zfill_id}_entity_{entity["type"]}_{index}'

        for point in entity["fields"]["point"]:
            point_var_name = f"{var_name}_to"
            points_var_declr = f'{points_var_declr}\nBN_DATA_EWRAM static const bn::pair<bn::string<10>, bn::fixed_point> {point_var_name} = bn::pair<bn::string<10>, bn::fixed_point>("to", bn::fixed_point({point["to"]["cx"]}, {point["to"]["cy"]}));'
            points_var_list.append(f"&{point_var_name}")

        for str_field in entity["fields"]["str"]:
            if "speech" not in str_field:
                continue  # TODO get the other one too
            if len(str_field["speech"]) > STRING_METADATA_SIZE:
                print(
                    f"increasing STRING_METADATA_SIZE to something more than {STRING_METADATA_SIZE}"
                )
                raise BaseException
            string_var_name = f"{var_name}_speech"
            strings_var_declr = f'{strings_var_declr}\nBN_DATA_EWRAM static const bn::pair<bn::string<10>, bn::string<{STRING_METADATA_SIZE}>> {string_var_name} = bn::pair<bn::string<10>, bn::string<{STRING_METADATA_SIZE}>>("speech", "{str_field["speech"]}");'
            strings_var_list.append(f"&{string_var_name}")

        entities_var_list.append(f"&{var_name}")
        coords_value = ""
        coords_var_name = "nullptr"
        if len(points_var_list) > 0:
            coords_value = f"""BN_DATA_EWRAM static const bn::pair<bn::string<10>, bn::fixed_point> *{var_name}_coords[] = {str(points_var_list).replace('[', '{').replace(']', '}').replace("'", '')};"""
            coords_var_name = f"{var_name}_coords"

        strings_value = ""
        strings_var_name = "nullptr"
        if len(strings_var_list) > 0:
            strings_value = f"""BN_DATA_EWRAM static const bn::pair<bn::string<10>, bn::string<{STRING_METADATA_SIZE}>> *{var_name}_strings[] = {str(strings_var_list).replace('[', '{').replace(']', '}').replace("'", '')};"""
            strings_var_name = f"{var_name}_strings"

        entities_var_declar = f"""

{points_var_declr}
{strings_var_declr}
{coords_value}
{strings_value}
{entities_var_declar}\nBN_DATA_EWRAM static const Entity {var_name} = Entity(
    {id},
    EntityType::{entity["type"]},
    {entity["location"][0]},
    {entity["location"][1]},
    {coords_var_name},
    {strings_var_name},
    {len(points_var_list)},
    0
);
"""

    with open(filename, "w") as cpp_level:
        cpp_level.write(
            f"""
#ifndef COLLIE_DEFENCE_GBA_LEVEL_{zfill_id}_H
#define COLLIE_DEFENCE_GBA_LEVEL_{zfill_id}_H

#include "bn_regular_bg_items_levels_{zfill_id}.h"
#include "bn_utility.h"
#include "bn_string.h"
#include "level.h"
#include "entity.h"
#include "generated/world_config.h"

namespace cd {{
    {entities_var_declar}
    static const Entity* entities_{level['int_identifier']}[] = {str(entities_var_list).replace('[', '{').replace(']', '}').replace("'", '')};
    static const int int_grid_{level['int_identifier']}[] = {str(level['int_grid']).replace('[', '{').replace(']', '}')};
    BN_DATA_EWRAM static Level level_{level['int_identifier']} = Level(
        bn::regular_bg_items::levels_{zfill_id},
        int_grid_{level['int_identifier']},
        {level['world_x']},
        {level['world_y']},
        entities_{level['int_identifier']},
        {len(entities_var_list)}
    );

#endif
}}"""
        )
print("Done!")