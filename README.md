# FeatureCloud K-anonymity App 

## Description
The FeatureCloud K-anonimity App provides the capability for anonymizing sensitive data using K-anonymity and other approches (e.g. l-diversity, t-closeness). The app integrates the Java API provided by the [ARX – Data Anonymization Tool](https://arx.deidentifier.org/development/api/) with Python and lets the user assign hierarchies through CSV files to perform data transformation methods. 

## Input 
- data.csv - containing the original dataset (columns: features; rows: samples)
- hierarchies_folder - folder containing the csv files corresponding to the hierarchies of quasi-identifying attributes.

## Output
- anom_data.csv - containing the anonymized dataset generated with the given privacy models and hierarchies.

## Workflow
Can be combined with the following apps:
- Post: 
  - Preprocessing apps (e.g. Cross-validation, Normalization ...) 
  - Various analysis apps (e.g. Logistic Regression, Linear Regression ...)

## Config  
Use the config file to set the parameters for the anonymization. Upload it together with your data that will be anonymized. 

```
fc_anonymization:
  local_dataset:
    data: data.csv
    sep: ;
    hierarchies_folder: Hierarchies
  arx:
    attributes:
      age: 
        data_type: INTEGER #Optional                             
        attribute_type: QUASI_IDENTIFYING              
        hierarchy_file: data_age_hierarchy.csv
      zipcode: 
        data_type: DECIMAL #Optional
        attribute_type: QUASI_IDENTIFYING
        hierarchy_file: data_zipcode_hierarchy.csv
      disease: 
        data_type: STRING #Optional
        attribute_type: QUASI_IDENTIFYING
        hierarchy_file: data_disease_hierarchy.csv
      salary:
        data_type: INTEGER #Optional 
        attribute_type: SENSITIVE
        privacy_model: OrderedDistanceTCloseness
    models: 
      KAnonymity:
        k: 2
      OrderedDistanceTCloseness:
        t: 0.375
    config: 
      SuppressionLimit: 0
  result:
    file: anom_data.csv
```

### Config File Options 

#### Local dataset
The input data should include a CSV file containing the dataset to be anonymized and a folder containing the hierarchy for each quasi-identifier as a CSV file. The user should specify a unique delimiter for all CSV files. 

#### ARX - Attributes
For each attribute in the input dataset, the user can define the following parameters: 
- `data_type`: indicates the data type of the attribute. The possible data types are: DATE, DECIMAL, INTEGER, ORDERED_STRING and STRING. If not 
given the data type is inferred by the program.
- `attribute_type`: indicates the type of an attribute. The possible values include: IDENTIFYING, QUASI_IDENTIFYING, SENSITIVE AND INSENSITIVE. The default value if not given for an attribute is IDENTIFYING.

The IDENTIFYING attributes are attributes that contain personal identifiers (e.g. name, address, date of birth). These attributes are removed from the dataset. 

The QUASI_IDENTIFYING attributes are attributes that link with further information can be used for the reidentification of an individual. For these attributes, the user can imposed constraints by generalizing attribute values based on hierarchies. For setting a hierarchy to an attribute, the user should include the following parameter:
- `hierachy_file`: indicates the name of the CSV file in the hierarchies folder provided in the local dataset configuration.

The SENSITIVE attributes are attributes that contain confidential information about an individual. For protecting these attributes, ARX provides some privacy models such as t-closeness or l-diversity, which the user can specified using the following parameter:
- `privacy_model`: indicates the name of the privacy model used for a sensitive attribute. The models names can be found in the [ARX package](https://arx.deidentifier.org/wp-content/uploads/javadoc/current/api/index.html) under the criteria class and the ones supported are listed under the Privacy Models section.

The INSENSITIVE attributes are attributes that can be kept unmodified.

The hierarchies provided in the CSV files can be of four types:
1. Masking-based hierarchies
2. Interval-based hierarchies
3. Order-based hierarchies
4. Date-based hierarchies

For more information on how to create the hierarchies, please refer to the [official documentation of ARX for configuration.](https://arx.deidentifier.org/anonymization-tool/configuration/) In particular, the section Creating generalization hierarchies. 

#### ARX - Privacy Models
The privacy models should include the name of the model and the corresponding parameters. 

For the quasi-identifying attributes, the privacy model used is "K-KAnonymity" and the required parameter is "k". For the user to use this model, the config file should include the following under the section models:
```
    KAnonymity:
        k: 2
```

Furthermore, for sensitive attributes the privacy models that can be used are the following: 
   - BasicBLikeness
   - DDisclosurePrivacy
   - DistinctLDiversity
   - EntropyLDiversity
   - EqualDistanceTCloseness
   - HierarchicalDistanceTCloseness
   - LDiversity
   - OrderedDistanceTCloseness
   - RecursiveCLDiversity
   - TCloseness

If an user has specified the privacy model required for a sensitive attribute, the section models should also include the name of this model and its parameters. For instance, the "salary" attribute in the config file has the privacy model "OrderedDistanceTCloseness". Therefore, the config file should include under the section models:
```
    OrderedDistanceTCloseness:
        t: 0.375
```

For more information of the parameters for each model, please refer to the [ARX package](https://arx.deidentifier.org/wp-content/uploads/javadoc/current/api/index.html) under the criteria class.

#### ARX - Config
ARX also provides further configuration possibilites. This app lets the user set a supression limit in the configuration as follows:

```
    config: 
        SuppressionLimit: 0
```        

#### Result 
The output data should include a CSV file containing the anonymized data.
