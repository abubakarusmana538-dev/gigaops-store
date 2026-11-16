REGISTRY ?= gigaops
TAG      ?= v1

.PHONY: build push helm-lint kustomize-check deploy-plain deploy-helm-dev deploy-kustomize-dev clean-plain
build:
	docker build -t $(REGISTRY)/gigaops-frontend:$(TAG) services/frontend
	docker build -t $(REGISTRY)/gigaops-product:$(TAG)  services/product-service
	docker build -t $(REGISTRY)/gigaops-order:$(TAG)    services/order-service
push:
	docker push $(REGISTRY)/gigaops-frontend:$(TAG)
	docker push $(REGISTRY)/gigaops-product:$(TAG)
	docker push $(REGISTRY)/gigaops-order:$(TAG)
helm-lint:
	helm lint helm/gigaops-store
kustomize-check:
	for e in dev test prod; do kubectl kustomize kustomize/overlays/$$e > /dev/null && echo "$$e ok"; done
deploy-plain:
	kubectl apply -f k8s/base/
deploy-helm-dev:
	helm upgrade --install gigaops-dev helm/gigaops-store -n gigaops-dev --create-namespace -f helm/gigaops-store/values-dev.yaml
deploy-kustomize-dev:
	kubectl create namespace gigaops-dev --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -k kustomize/overlays/dev
clean-plain:
	kubectl delete namespace gigaops-store
