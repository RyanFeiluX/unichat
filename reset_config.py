import os
import toml, tomlkit
from tomlkit import TOMLDocument
from backend.logging_config import setup_logging
import argparse

logger = setup_logging()
app_root = os.path.abspath(os.path.dirname(__file__))

def copy_dictvalues(obj:TOMLDocument, dst: dict, src: dict):
    for k,v in dst.items():
        if type(v).__name__ in ['str', 'int']:
            try:
                obj[k] = src[k]
            except KeyError:
                logger.error(f'Key {k} is missing from source dict object.')
            except Exception as ee:
                logger.error(f'{repr(ee)}')
        elif type(v).__name__ in ['dict']:
            copy_dictvalues(obj[k], v, src[k])
        else:
            continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--dynamic-config', dest='dyn_config', type=str, required=True, help="Dynamic config")
    parser.add_argument('--factory-config', dest='fac_config', type=str, required=True, help="Factory config")
    args = parser.parse_args()

    logger.info(f'Config is reset for distribution purpose.')

    dynamic_cfg_path = args.dyn_config
    if not os.path.exists(dynamic_cfg_path):
        logger.error(f"Could not find {dynamic_cfg_path}")

    # Load config parameters
    dyn_cfg = toml.load(dynamic_cfg_path)
    with open(dynamic_cfg_path, "r", encoding="utf-8") as f:
        dynamic_cfg = tomlkit.parse(f.read())

    factory_cfg_path = os.path.join(app_root, "backend", "factory.toml")
    if not os.path.exists(factory_cfg_path):
        logger.error(f"Could not find {factory_cfg_path}")

    # Load factory defaults
    fac_cfg = toml.load(factory_cfg_path)

    copy_dictvalues(dynamic_cfg, dyn_cfg, fac_cfg)

    with open(dynamic_cfg_path, "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(dynamic_cfg))
        f.flush()

    logger.info(f'Config reset complete.')