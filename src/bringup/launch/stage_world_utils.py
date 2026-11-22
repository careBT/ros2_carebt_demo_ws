import os
import re
import tempfile

import yaml


def resolve_world(world, bringup_dir):
    """Absolute path of a world name (in bringup/worlds, .world optional) or path."""
    if not os.path.isabs(world):
        world = os.path.join(bringup_dir, 'worlds', world)
    if not world.endswith('.world'):
        world += '.world'
    if not os.path.isfile(world):
        raise RuntimeError(f'World file {world} does not exist')
    return world


def read_world(path):
    # world files use '#' line comments
    with open(path) as f:
        return re.sub(r'#.*', '', f.read())


def find_map_yaml(world_file, text):
    """maps/<name>.yaml next to the world file, <name> taken from the floorplan bitmap."""
    match = re.search(r'\bbitmap\s+"([^"]+)"', text)
    if not match:
        raise RuntimeError(f'No bitmap entry found in world file {world_file}')
    name = os.path.splitext(os.path.basename(match.group(1)))[0]
    map_yaml = os.path.join(os.path.dirname(world_file), 'maps', name + '.yaml')
    if not os.path.isfile(map_yaml):
        raise RuntimeError(f'Map file {map_yaml} for world {world_file} does not exist')
    return map_yaml


def find_robot_pose(text):
    """Pose (x, y, yaw[rad]) of the first top-level pioneer* model, or None."""
    for match in re.finditer(r'^(?!\s*define\b)\s*pioneer\w*\s*\(', text, re.MULTILINE):
        depth, end = 1, match.end()
        while end < len(text) and depth:
            depth += {'(': 1, ')': -1}.get(text[end], 0)
            end += 1
        pose = re.search(r'\bpose\s*\[([^\]]*)\]', text[match.end():end])
        if pose:
            values = [float(v) for v in pose.group(1).split()]
            if len(values) >= 4:
                return values[0], values[1], values[3] * 3.141592653589793 / 180.0
    return None


def write_amcl_initial_pose(params_file, world_name, pose):
    """Copy of the Nav2 params file with the amcl initial pose set to pose."""
    with open(params_file) as f:
        params = yaml.safe_load(f)
    params['amcl']['ros__parameters']['initial_pose'].update(
        {'x': pose[0], 'y': pose[1], 'yaw': pose[2]})
    out = os.path.join(tempfile.gettempdir(), f'{world_name}_nav2_params.yaml')
    with open(out, 'w') as f:
        yaml.safe_dump(params, f)
    return out
