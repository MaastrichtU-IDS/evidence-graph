# Evidence Graph API Documentation 

The evidence graph service creates a detailed provenance trace of the requested identifier. The returned evidence graph is a json-ld representation of the computations and inputs that went into creating the requested object. 


# Endpoints
 - **/{PID}**


# /{PID}

## GET

Returns evidence graph for requested PID

```console
$ curl http://clarklab.uvarc.io/eg/ark:99999/ra1-ndom-32-ark 
```
