---
name: traefik-subpath-docker-compose
description: >
  Traefik reverse proxy를 통해 서브패스(/path)로 서비스를 노출하는 docker-compose 구성 패턴.
  Streamlit, phpMyAdmin 등 서브패스 인식이 필요한 앱의 라벨/환경변수 설정 포함.
triggers:
  - traefik으로 프록시
  - 서브패스(/xxx)로 라우팅
  - docker-compose release 구성
  - stripprefix 미들웨어
  - phpmyadmin subpath
tags:
  - traefik
  - docker-compose
  - subpath
  - proxy
  - streamlit
  - phpmyadmin
---

# Traefik 서브패스 docker-compose 배포 패턴

## 핵심 원칙

Traefik은 기본적으로 PathPrefix를 strip하지 않음.
`/jms_pma`로 라우팅해도 phpMyAdmin은 `/jms_pma/index.php`를 받아 Not Found 반환.
반드시 `stripprefix` 미들웨어를 함께 설정해야 함.

## Streamlit 서브패스 설정

Dockerfile CMD에 `--server.baseUrlPath` 지정:
```dockerfile
CMD ["streamlit", "run", "streamlit_app.py",
     "--server.port=8501",
     "--server.headless=true",
     "--server.baseUrlPath=/jms"]
```

Traefik 라벨 (strip 불필요 — Streamlit이 baseUrlPath 자체 처리):
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.jms.rule=PathPrefix(`/jms`)"
  - "traefik.http.routers.jms.entrypoints=web"
  - "traefik.http.services.jms.loadbalancer.server.port=8501"
```

## phpMyAdmin 서브패스 설정

두 가지를 모두 설정해야 정상 동작:
1. `stripprefix` 미들웨어 — prefix를 제거한 경로를 phpMyAdmin에 전달
2. `PMA_ABSOLUTE_URI` — phpMyAdmin 내부 링크/리다이렉트 기준 URL

```yaml
phpmyadmin:
  image: phpmyadmin:latest
  environment:
    - PMA_HOST=db
    - PMA_PORT=3306
    - PMA_ABSOLUTE_URI=http://<host>/<prefix>/
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.jms-pma.rule=PathPrefix(`/jms_pma`)"
    - "traefik.http.routers.jms-pma.entrypoints=web"
    - "traefik.http.services.jms-pma.loadbalancer.server.port=80"
    - "traefik.http.middlewares.jms-pma-strip.stripprefix.prefixes=/jms_pma"
    - "traefik.http.routers.jms-pma.middlewares=jms-pma-strip"
```

## 네트워크 구성 패턴

Traefik이 붙는 외부 네트워크 + 내부 서비스 전용 네트워크 분리:

```yaml
networks:
  proxy:
    external: true
    name: <traefik-network-name>   # 실제 traefik 네트워크명 확인 필요
  internal:
    driver: bridge
```

- `proxy` 네트워크: Traefik ↔ 앱/phpmyadmin (외부 노출 서비스만)
- `internal` 네트워크: 앱 ↔ DB (DB는 proxy에 붙이지 않음)

## MariaDB healthcheck

app이 DB 준비 전 기동되는 것을 방지:
```yaml
db:
  image: mariadb:11.8.2-noble
  healthcheck:
    test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 30s

app:
  depends_on:
    db:
      condition: service_healthy
```

## Pitfalls

- **stripprefix 누락**: Traefik은 PathPrefix를 strip하지 않음. Apache 기반 앱(phpMyAdmin)은 `/prefix/` 경로를 인식 못해 `Not Found` 반환.
- **PMA_ABSOLUTE_URI 누락**: stripprefix만 설정하면 phpMyAdmin 내부 링크가 루트(`/`) 기준으로 생성되어 CSS/JS 로드 실패, 로그인 후 루트로 리다이렉트됨.
- **PMA_ABSOLUTE_URI 끝 슬래시**: 반드시 `/`로 끝나야 함 (`http://host/pma/` O, `http://host/pma` X).
- **proxy 네트워크 사전 생성 필요**: `docker network create proxy` (또는 traefik compose up) 먼저.
- **traefik 네트워크명**: `proxy`가 아닐 수 있음. `docker network ls`로 실제명 확인 후 `name:` 필드에 반영.

## 전체 템플릿

`templates/docker-compose-traefik-subpath.yaml` 참고.
