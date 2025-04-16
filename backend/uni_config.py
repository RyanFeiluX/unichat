import os, sys
from pydantic import BaseModel
from typing import List, Dict, Union
from dotenv import load_dotenv, find_dotenv
import toml
import tomlkit  # Import tomlkit for round-trip parsing
from utils import check_model_avail


class DeploymentProfile(BaseModel):
    llm_provider: str = None
    llm_model: str = None
    emb_provider: str = None
    emb_model: str = None

class UniConfig():

    def __init__(self, app_root, logger):
        self.app_root = app_root
        self.logger = logger
        self.scfg_path = os.path.join(app_root, "backend", "sta_config.toml")
        self.dcfg_path = os.path.join(app_root, "backend", "dyn_config.toml")
        self.factory_cfg_path = os.path.join(app_root, "backend", "factory.toml")
        self._validate()
        self.scfg = self.load_static_config()
        self.dcfg = self.load_dynamic_config()
        self.factory_cfg = self.load_factory_config()
        # Ensure dynamic configuration is merged with factory defaults
        self.merge_config(self.dcfg, self.factory_cfg)
        # Load env variables from local .env file. Several parameters are there, including API_KEY.
        dotenv_path = find_dotenv(filename='.env', raise_error_if_not_found=False)
        if dotenv_path:
            logger.info(f'dotenv={dotenv_path}')
            _ = load_dotenv(dotenv_path=os.path.abspath(dotenv_path))
        else:
            logger.info(f'No dotenv found')
        self.santize()
        self._changes_suspense = 0

    @property
    def changes_suspense(self):
        return self._changes_suspense > 0

    def _validate(self):
        cfg_error_cnt = 0
        if not os.path.exists(self.scfg_path):
            self.logger.error(f"Could not find {self.scfg_path}")
            cfg_error_cnt += 1
        if not os.path.exists(self.dcfg_path):
            self.logger.error(f"Could not find {self.dcfg_path}")
            cfg_error_cnt += 1
        if not os.path.exists(self.factory_cfg_path):
            self.logger.error(f"Could not find {self.factory_cfg_path}")
            cfg_error_cnt += 1
        if cfg_error_cnt > 0:
            self.logger.error(f'Application detected above error{"s" if cfg_error_cnt > 1 else ""}. Quit...')
            sys.exit("Configuration failure")

    def load_static_config(self):
        return toml.load(self.scfg_path)

    def load_dynamic_config(self):
        return toml.load(self.dcfg_path)

    def load_factory_config(self):
        return toml.load(self.factory_cfg_path)

    # Merge dcfg with factory_cfg for missing or empty fields
    def merge_config(self, target_cfg, source_cfg):
        """
        Merge the target configuration with the factory defaults.

        This function ensures that empty fields in the target configuration
        are filled with values from the factory configuration.

        Args:
            target_cfg (dict): The target configuration dictionary to be updated.
            source_cfg (dict): The factory configuration dictionary containing default values.
        """
        for section, values in target_cfg.items():
            if values is None:
                target_cfg[section] = source_cfg[section] if section in source_cfg else None
            elif isinstance(values, dict):
                if section not in source_cfg:
                    continue
                self.merge_config(values, source_cfg[section])
            elif isinstance(values, list):
                if section not in source_cfg:
                    continue
                if values is []:
                    target_cfg[section] = source_cfg[section]
            elif isinstance(values, str):
                if section not in source_cfg:
                    continue
                if values == '' or values is None:
                    target_cfg[section] = source_cfg[section]

    def update_llmconfig(self, llmProvider, llmModel):
        # Load the original TOML file with tomlkit to preserve structure and comments
        with open(os.path.join(self.app_root, "backend", "dyn_config.toml"), "r", encoding="utf-8") as f:
            dyn_config = tomlkit.parse(f.read())

        # Update the TOML structure with new values
        dyn_config['Deployment']['LLM_PROVIDER'] = llmProvider
        dyn_config['Deployment']['LLM_MODEL'] = llmModel

        # Write the updated TOML back to the file
        with open(os.path.join(self.app_root, "backend", "dyn_config.toml"), "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(dyn_config))
            f.flush()
            self._changes_suspense += 1

    def retrieve_llmconfig(self):
        # llm
        llm_provider = self.dcfg['Deployment']['LLM_PROVIDER'].upper()  # os.getenv("LLM_PROVIDER")
        if llm_provider:
            self.logger.info(f'LLM provider : {llm_provider}')
            # llm_model = os.getenv("LLM_MODEL") or os.getenv(f'{llm_provider}_LLM_MODEL')
            llm_model = (self.dcfg['Deployment']['LLM_MODEL']
                         or self.scfg['Providers'][llm_provider][f'{llm_provider}_LLM_MODEL'].split(',')[0])
            self.logger.info(f'LLM model : {llm_model}')
            if not llm_model:
                self.logger.critical(f'Please configure at least a model for {llm_provider}.')
        else:
            llm_model = None
        return llm_provider, llm_model

    def get_default_llmconfig(self):
        return self.scfg['Default']['llmProvider'], self.scfg['Default']['llmModel']

    def get_default_embconfig(self):
        return self.scfg['Default']['embProvider'], self.scfg['Default']['embModel']

    def get_documents(self)->list:
        docs = self.dcfg['Knowledge']['DOCUMENTS'].split(',')
        return [d.strip() for d in docs]

    def get_robot_desc(self):
        return self.dcfg['Knowledge']['ROBOT_DESC']

    def update_knowledge_base(self, documents: list|None = None, robot_desc: str|None = None):
        if documents or robot_desc:
            # Load the original TOML file with tomlkit to preserve structure and comments
            with open(os.path.join(self.app_root, "backend", "dyn_config.toml"), "r", encoding="utf-8") as f:
                dyn_config = tomlkit.parse(f.read())

            # Update the TOML structure with new values
            if documents:
                dyn_config['Knowledge']['DOCUMENTS'] = documents
            if robot_desc:
                dyn_config['Knowledge']['ROBOT_DESC'] = robot_desc.strip()

            # Write the updated TOML back to the file
            with open(os.path.join(self.app_root, "backend", "dyn_config.toml"), "w", encoding="utf-8") as f:
                f.write(tomlkit.dumps(dyn_config))
                f.flush()
                self._changes_suspense += 1

    def update_embconfig(self, embProvider, embModel):
        # Load the original TOML file with tomlkit to preserve structure and comments
        with open(self.dcfg_path, "r", encoding="utf-8") as f:
            dyn_config = tomlkit.parse(f.read())

        # Update the TOML structure with new values
        dyn_config['Deployment']['EMB_PROVIDER'] = embProvider
        dyn_config['Deployment']['EMB_MODEL'] = embModel

        # Write the updated TOML back to the file
        with open(self.dcfg_path, "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(dyn_config))
            f.flush()
            self._changes_suspense += 1

    def retrieve_embconfig(self):
        emb_provider = self.dcfg['Deployment']['EMB_PROVIDER'].upper()  # os.getenv('EMB_PROVIDER')
        if emb_provider:
            self.logger.info(f'Embedding provider : {emb_provider}')
            emb_model = self.dcfg['Deployment']['EMB_MODEL']  # os.getenv(f"EMB_MODEL")
            self.logger.info(f'Embedding model : {emb_model}')
            if not emb_model:
                self.logger.critical(f'Please configure at least a model for {emb_provider}.')
        else:
            emb_model = None
        return emb_provider, emb_model

    def santize(self):
        # cfg = UniConfig()
        llm_provider, llm_model = self.retrieve_llmconfig()

        if (not llm_provider) or (not check_model_avail(llm_model)):
            self.update_llmconfig(*self.get_default_llmconfig())

            self.logger.error(f'Model {llm_model} is not locally found. Please run \"Ollama pull {llm_model}\" offline.')
            self.logger.warning(f'Please close the app and download model {llm_model} offline.')
            while True:
                pass

        emb_provider, emb_model = self.retrieve_embconfig()
        if (not emb_provider) or (not check_model_avail(emb_model)):
            self.update_embconfig(*self.retrieve_embconfig())

            self.logger.error(f'Model {emb_model} is not locally found. Embedding config shall fall back.')
            self.logger.warning(f'Please close the app and download model {emb_model} offline.')
            while True:
                pass

    def aggregate_provider_profile(self):
        options: list = []
        for p in self.scfg['Providers'].keys():
            options.append({'provider': p,
                            'llm_model': self.scfg['Providers'][p][f'{p.upper()}_LLM_MODEL'].split(','),
                            'emb_model': self.scfg['Providers'][p][f'{p.upper()}_EMB_MODEL'].split(','),
                            'prov_intro': self.scfg['Providers'][p][f'{p.upper()}_INTRO']}
                           )
        return options

    def get_deployment_profile(self)->Dict[str, str]:
        sel = dict()
        sel['llm_provider']= self.dcfg['Deployment']['LLM_PROVIDER']
        sel['llm_model']= self.dcfg['Deployment']['LLM_MODEL']
        sel['emb_provider']= self.dcfg['Deployment']['EMB_PROVIDER']
        sel['emb_model']= self.dcfg['Deployment']['EMB_MODEL']
        return sel

    def update_deployment_profile(self, options: DeploymentProfile):
        self.dcfg['Deployment']['LLM_PROVIDER'] = options.llm_provider
        self.dcfg['Deployment']['LLM_MODEL'] = options.llm_model
        self.dcfg['Deployment']['EMB_PROVIDER'] = options.emb_provider
        self.dcfg['Deployment']['EMB_MODEL'] = options.emb_model

        # Load the original TOML file with tomlkit to preserve structure and comments
        with open(os.path.join(self.app_root, "backend", "dyn_config.toml"), "r", encoding="utf-8") as f:
            dyn_config = tomlkit.parse(f.read())

        # Update the TOML structure with new values
        dyn_config['Deployment']['LLM_PROVIDER'] = options.llm_provider
        dyn_config['Deployment']['LLM_MODEL'] = options.llm_model
        dyn_config['Deployment']['EMB_PROVIDER'] = options.emb_provider
        dyn_config['Deployment']['EMB_MODEL'] = options.emb_model

        # Write the updated TOML back to the file
        with open(os.path.join(self.app_root, "backend", "dyn_config.toml"), "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(dyn_config))
            f.flush()
            self._changes_suspense += 1
