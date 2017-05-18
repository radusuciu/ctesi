Ctesi is a project meant to simplify processing and quantification of chemoproteomic mass spectrometry data in the [Cravatt lab](https://www.scripps.edu/cravatt). The following are automated:
- Conversion of `.raw` files to `.ms2` and `mzXML` formats
- Submission to an instance of [IP2](http://www.integratedproteomics.com/) maintained at [The Scripps Research Institute](https://scripps.edu/)
- Quantification of data with in-house software (cimage)

## Dev setup notes

Ctesi requires a copy of the `cimage-minimal` project, to be placed alongside it.

On development instances you must create a file `config/secrets.override.yml`. This will by default not be entered into version control. It must contain credentials for accessing Active Directory. There is an example file in `config/secrets.yml`.

You must also mount an NFS share that is accessible by a `cravatt-rawprocessor` (not included here) instance. An example mount commmand is included in `config/mount-nfs.example.sh`. This command must be issued with root privileges.