# generic_saml_logon
Login and intercept one-time-use SAMLResponse before it's sent to the SP.  I use this for APIs that need the SAMLResponse value submitted to a different endpoint than the IdP redirects to.

# SECURITY NOTE:
I wrote the .py files.  You have my word that they don't do anything nefarious.  Even so, I recommend that you perform
your own static analysis and supply chain testing before use.  Many libraries are imported that are not in my own control.

# usage
```
$ python generic_saml_logon.py 
usage: generic_saml_logon.py [-h] --sp_url SP_URL --username USERNAME --password PASSWORD [--proxies PROXIES]
```

# example
```
$ python generic_saml_logon.py --sp_url https://app.example.com/sso/saml/start --username MyUsername --password MyPassword

```
