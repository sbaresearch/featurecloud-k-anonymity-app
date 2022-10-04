from FeatureCloud.app.engine.app import AppState, app_state, Role, LogLevel
from FeatureCloud.app.engine.app import State as op_state
from CustomStates import ConfigState
import os
import pandas as pd
from jpype import startJVM
import jpype.imports

# App name
name='fc_anonymization'

@app_state('initial', role=Role.BOTH, app_name=name)
class LoadData(ConfigState.State):
    
    def register(self):
        self.register_transition('WriteAnonymizedData') 

    def run(self):   
        self.lazy_init()
        self.read_config()
        self.finalize_config()
        startJVM(classpath='libarx-3.9.0.jar')
        print('The JVM is running ...')
        data=self.read_data()
        data=self.configure_attributes(data)
        anonymized_data=self.anonymize_data(data)
        output_file= f"{self.output_dir}/{self.config['result']['file']}"
        self.store('output_file', output_file)
        self.store('anonymized_data', anonymized_data)
        return 'WriteAnonymizedData'  

    def read_data(self):
        # --------------- Java imports ----------------#
        from org.deidentifier.arx import Data
        from java.nio.charset import StandardCharsets
        # ---------------------------------------------#
        input_files = self.load('input_files')
        data_file = input_files['data'][0]
        hierarchies_folder = input_files['hierarchies_folder'][0]
        delimiter = self.config['local_dataset']['sep']
        format = data_file.split('.')[-1].strip()
        privacy_models = dict()
        self.store('hierarchies_path', hierarchies_folder)
        self.store('delimiter', delimiter)
        self.store('privacy_models', privacy_models)
        if format == 'csv' or format == 'txt':
            df= Data.create(data_file, StandardCharsets.UTF_8, delimiter)
        else:
            self.log(f'The file format {format} is not supported', LogLevel.ERROR)
            self.update(state=op_state.ERROR)
        return df

    def configure_attributes(self,data):
        attributes = self.config['arx'].get('attributes', False)
        if attributes:
            for attr in attributes:
                print("Setting Attribute.............")
                print(attr)
                config_attr=attributes[attr]
                if 'attribute_type' in config_attr:
                    attr_type = self.parse_attribute_type(config_attr, attr)
                    data.getDefinition().setAttributeType(attr, attr_type)
                if 'data_type' in config_attr:
                    data_type = self.parse_data_type(config_attr['data_type'], attr)
                    data.getDefinition().setDataType(attr, data_type)        
        else:
            self.log(f'The attributes configuration is not specified. Please provide the attribute type for each attribute.', LogLevel.ERROR)
            self.update(state=op_state.ERROR) 
        return data

    def parse_attribute_type(self, config_attr, attr_str):
        #---------------- Java imports ----------------#
        from org.deidentifier.arx import AttributeType
        from org.deidentifier.arx.AttributeType import Hierarchy
        from java.nio.charset import StandardCharsets
        #----------------------------------------------#
        hierarchies = self.load('hierarchies')
        attr_type=config_attr['attribute_type']
        if (attr_type=='IDENTIFYING'):
            return AttributeType.IDENTIFYING_ATTRIBUTE
        elif(attr_type=='INSENSITIVE'):
            return AttributeType.INSENSITIVE_ATTRIBUTE
        elif(attr_type=='QUASI_IDENTIFYING'):
            if 'hierarchy_file' in config_attr:
                hierarchies_folder=self.load('hierarchies_path')
                hierarchy_path=os.path.join(hierarchies_folder,config_attr['hierarchy_file'])
                delimiter= self.load('delimiter')
                return  Hierarchy.create(hierarchy_path, StandardCharsets.UTF_8, delimiter)
            else:
                self.log(f'For the attribute type QUASI_IDENTIFYING specified for {attr_str} the hierarchy_file should be included in the yml configuration', LogLevel.ERROR)
                self.update(state=op_state.ERROR)
        elif (attr_type=='SENSITIVE'):
            if 'privacy_model' in config_attr:
                privacy_models=self.load('privacy_models')
                privacy_models[config_attr['privacy_model']] = attr_str
                self.store('privacy_models', privacy_models)    
            else:
                self.log(f'For the attribute type SENSITIVE specified for {attr_str} the privacy_model should be included in the yml configuration', LogLevel.ERROR)
                self.update(state=op_state.ERROR)
            if 'hierarchy_file' in config_attr:
                hierarchies_folder=self.load('hierarchies_path')
                hierarchy_path=os.path.join(hierarchies_folder,config_attr['hierarchy_file'])
                delimiter= self.load('delimiter')
                hierarchy = Hierarchy.create(hierarchy_path, StandardCharsets.UTF_8, delimiter)
                self.store(f'hierarchy_{attr_str}', hierarchy)
            return AttributeType.SENSITIVE_ATTRIBUTE
        else:
            self.log(f'The attribute type of {attr_str} is not supported', LogLevel.ERROR)
            self.update(state=op_state.ERROR)

    def parse_data_type(self, attr_type, attr_str):
        #---------------- Java imports ----------------#
        from org.deidentifier.arx import DataType
        #----------------------------------------------#
        if (attr_type=='DECIMAL'):
            return DataType.DECIMAL
        elif(attr_type=='STRING'):
            return DataType.STRING
        elif(attr_type=='ORDERED_STRING'):
            return DataType.INTEGER
        elif(attr_type=='INTEGER'):
            return DataType.INTEGER
        elif (attr_type=='DATE'):
            return DataType.DATE
        else:
            self.log(f'The data type of {attr_str} is not supported', LogLevel.ERROR)
            self.update(state=op_state.ERROR)

    def parse_privacy_models(self, params, model_str):
        #---------------- Java imports ----------------#
        import org
        from org.deidentifier.arx import criteria
        from jpype.types import JDouble, JInt
        from org.deidentifier.arx.criteria import HierarchicalDistanceTCloseness
        from org.deidentifier.arx.criteria import KAnonymity
        #----------------------------------------------#
        params_list=[]
        if (model_str == "KAnonymity"):
            if "k" not in params: 
                self.log(f'The privacy model {model_str} requires the parameter k', LogLevel.ERROR)
                self.update(state=op_state.ERROR)
            model = KAnonymity(JInt(params['k']))
        else:
            privacy_models=self.load('privacy_models')
            attr_str=privacy_models[model_str]
            if model_str not in privacy_models.keys():
                self.log(f'The privacy model {model_str} is not assigned to any attribute', LogLevel.ERROR)
                self.update(state=op_state.ERROR)
            elif (model_str ==  "HierarchicalDistanceTCloseness"):
                hierarchy=self.load(f'hierarchy_{attr_str}')
                if hierarchy is None:
                    self.log(f'The privacy model {model_str} requires a hierarchy assigned for the attribute {attr_str}', LogLevel.ERROR)
                    self.update(state=op_state.ERROR)
                if "t" not in params: 
                    self.log(f'The privacy model {model_str} requires the parameter t', LogLevel.ERROR)
                    self.update(state=op_state.ERROR)
                model = HierarchicalDistanceTCloseness(attr_str, JDouble(params['t']), hierarchy)
            else:
                params_list.append(f"'{attr_str}'")
                for key, val in params.items():
                    print(f'Setting parameter {key} = {val} for privacy model: {model_str}')
                    params_list.append(str(val))
                params_str=','.join(params_list)
                function_str=f"{criteria}.{model_str}({params_str})"
                model= eval(function_str)      
        return model

    def parse_configuration_parameters(self,config_params, config):
        #---------------- Java imports ----------------#
        from org.deidentifier.arx import ARXConfiguration
        from jpype.types import JDouble
        #----------------------------------------------#
        if "SuppressionLimit" in config_params: 
            config.setSuppressionLimit(JDouble(config_params['SuppressionLimit']))
        else:
            self.log(f'The parameters for the configuration provided are not supported.', LogLevel.ERROR)
            self.update(state=op_state.ERROR) 
        return config

    def anonymize_data(self, data):
        #---------------- Java imports ----------------#
        from org.deidentifier.arx import ARXConfiguration
        from org.deidentifier.arx import ARXAnonymizer
        #----------------------------------------------#
        models = self.config['arx'].get('models', False)
        if models:
            anonymizer = ARXAnonymizer()
            config = ARXConfiguration.create()
            for privacy_model in models:
                model=self.parse_privacy_models(models[privacy_model],privacy_model)
                config.addPrivacyModel(model)
        else:
            self.log(f'Privacy model(s) not specified. Please provide the privacy model(s) and their parameters in the yml configuration.', LogLevel.ERROR)
            self.update(state=op_state.ERROR) 
        config_params = self.config['arx'].get('config', False)
        if config_params:
           config=self.parse_configuration_parameters(config_params, config)
        result = anonymizer.anonymize(data, config)
        print(result.getOutput(False))
        return result
    

# This state is executed after the app instance is started.
@app_state(name='WriteAnonymizedData', role=Role.BOTH)
class WriteResults(AppState):
    def register(self):
        self.register_transition('terminal', Role.BOTH)

    def run(self):
        #---------------- Java imports ----------------#
        from org.deidentifier.arx import ARXResult
        #----------------------------------------------#
        output_file=self.load('output_file')
        anonymized_data=self.load("anonymized_data")
        delimiter= self.load("delimiter")
        anonymized_data.getOutput(False).save(output_file, delimiter)
        df_anom= pd.read_csv(output_file)
        print("Anonymized Successfully created!")
        print(df_anom.head())
        return 'terminal'