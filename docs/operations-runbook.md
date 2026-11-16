# Operations runbook

## Health and troubleshooting
| Symptom | Command |
| --- | --- |
| Pod not starting | `kubectl describe pod <pod> -n <ns>` |
| CrashLoopBackOff | `kubectl logs <pod> -n <ns> --previous` |
| Pending | `kubectl get events -n <ns> --sort-by=.lastTimestamp` |
| Service has no endpoints | `kubectl get endpoints -n <ns>` |
| Node NotReady | `kubectl describe node <n>`; `journalctl -u kubelet -n 100` |
| Image pull failure | `sudo crictl pull <image>` on the node |
| DNS | `kubectl run dns --rm -it --image=busybox:1.36 -- nslookup kubernetes.default` |

## Smoke test
```bash
kubectl -n <ns> run curl --rm -it --image=curlimages/curl -- sh
curl http://product-service:5001/products
curl -X POST http://order-service:5002/orders -H 'Content-Type: application/json' -d '{"product_id":1,"quantity":2}'
```
## Rollouts (plain / Kustomize)
```bash
kubectl -n <ns> set image deployment/product product=<user>/gigaops-product:v2
kubectl -n <ns> rollout status deployment/product
kubectl -n <ns> rollout undo deployment/product
```
## Rollouts (Helm)
```bash
helm history gigaops-dev -n gigaops-dev
helm rollback gigaops-dev 1 -n gigaops-dev
```
## Node maintenance
```bash
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
# patch / reboot
kubectl uncordon <node>
```
## Backups
- etcd: `etcdctl snapshot save` (see the 75-task lab, tasks 34-35), stored off-node.
- MySQL: `kubectl exec deploy/mysql -n <ns> -- sh -c 'mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" storedb' > backup.sql`
- Certificates: `sudo kubeadm certs check-expiration` (renew before 1 year).

## Rules of thumb
- Don't manage the same namespace with Helm and Kustomize at once.
- NodePort values are cluster-wide unique.
- Never commit kubeconfigs or real credentials.
