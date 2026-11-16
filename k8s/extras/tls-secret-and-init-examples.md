Self-signed TLS secret (from ALM lab):

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout tls.key -out tls.crt \
      -subj "/OU=gigaops/C=IN/L=HYD/CN=store.example.local"
    kubectl create secret tls store-tls --cert=tls.crt --key=tls.key -n gigaops-store

Reference it from the Ingress with `spec.tls[].secretName: store-tls`.
