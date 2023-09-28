# Convert2EBRF

A GUI application for converting files to EBRF.

## Developer information

### Building

This package is managed with the pdm tool.

### IDE configuration

To get code completions and avoid warnings for PySide6 features of snake_case and true_property you may need to regenerate the stub files. Run the following command:
```commandline
pyside6-genpyi all --feature snake_case true_property
```