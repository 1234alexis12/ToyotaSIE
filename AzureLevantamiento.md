# Guía de Levantamiento y Despliegue en Azure VM (Terminal y PowerShell)
**Sistema de Información de Gestión Comercial, Logística y Taller — SIG-Toyota**  
**Servidor Cloud:** Azure Virtual Machine (Ubuntu 24.04 LTS Gen2 — Standard_D2as_v4)  
**IP Pública de Producción:** `158.23.20.45`  
**Usuario Administrador:** `azureuser`  

---

## 1. Conexión Remota a la Máquina Virtual desde Windows PowerShell

Abre la consola de **Windows PowerShell** en tu computadora personal y ejecuta el siguiente comando:

```powershell
ssh azureuser@158.23.20.45
```

### Explicación técnica:
* `ssh`: Invoca el cliente nativo OpenSSH de Windows para establecer una sesión de terminal cifrada bajo el puerto TCP 22.
* `azureuser`: Es el nombre del usuario administrador configurado en la máquina virtual Linux de Azure.
* `@158.23.20.45`: Es la dirección IP pública fija asignada por Microsoft Azure en la región Mexico Central.
* **Autenticación:** El servidor solicitará ingresar la contraseña (`TOYOTAsie2026`). En Linux no se muestran asteriscos ni caracteres al escribir por seguridad; tras digitarla, presiona `Enter`.

---

## 2. Instalación de Dependencias del Sistema y Motor Docker

Una vez dentro de la terminal de Ubuntu (`azureuser@vm-toyota-sie:~$`), ejecuta el siguiente comando:

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
sudo usermod -aG docker $USER
```

### Explicación técnica de cada comando:
* `sudo`: Otorga privilegios de superusuario (*root*) requeridos para instalar software a nivel de sistema operativo.
* `apt update`: Actualiza el catálogo y los índices de los repositorios de paquetes de Ubuntu para garantizar la descarga de las versiones estables más recientes.
* `&&`: Operador lógico de control que asegura que el segundo comando solo se ejecute si el primero finalizó exitosamente (código de salida 0).
* `apt install -y`: Instala paquetes en modo no interactivo aceptando automáticamente las solicitudes de confirmación de espacio en disco.
* `docker.io`: Instala el demonio principal (*daemon*) y motor de ejecución de contenedores Docker en el sistema Linux.
* `docker-compose-v2`: Instala el plugin oficial de Docker Compose (versión 2 en Go) para gestionar la orquestación multi-contenedor mediante comandos `docker compose`.
* `git`: Sistema de control de versiones distribuido necesario para clonar el repositorio de código fuente del proyecto.
* `sudo usermod -aG docker $USER`: Agrega al usuario actual (`azureuser`) al grupo de seguridad `docker`, permitiendo administrar contenedores sin requerir anteponer `sudo` en sesiones futuras.

---

## 3. Clonación del Repositorio de Código Fuente

Descarga la última versión del proyecto directamente desde el repositorio oficial de GitHub y navega a la carpeta de trabajo:

```bash
git clone https://github.com/1234alexis12/ToyotaSIE.git
cd ToyotaSIE
```

### Explicación técnica:
* `git clone https://...`: Clona de forma íntegra el historial de commits, ramas y código fuente del repositorio `ToyotaSIE` en un subdirectorio local denominado `ToyotaSIE`.
* `cd ToyotaSIE`: Cambia el directorio de trabajo actual a la raíz del proyecto donde se ubica el manifiesto `docker-compose.yml`.

---

## 4. Configuración Segura de Variables de Entorno (Jira Cloud)

Por directrices de seguridad (norma ISO 27001), los tokens privados y contraseñas de APIs externas están excluidos del control de versiones en el archivo `.gitignore`. Por ello, se genera el archivo `.env` en el servidor ejecutando el siguiente bloque de comandos:

```bash
cat << 'EOF' > .env
JIRA_BASE_URL=https://toyota-sie.atlassian.net
JIRA_EMAIL=luqueanthony26@gmail.com
JIRA_API_TOKEN=ATATT3xFfGF0UU-shpLHLQqr08_6zvGygm56Ziu21hIL9k4vT0gP5tobAMHEjyZh5Q0aAOcrbN63nmSZJaHZsVqARDdd9gtMe6pu2BPUGu-D4QzIgcoK-6cL6JOL2OPE0j3SG4Rc755N4Uxa5Bu1uFTt1HIwUgErA28HYhXsAQx4Ehyw1WywfiE=7AC84FC2
JIRA_PROJECT_KEY=PROJ
JIRA_ISSUE_TYPE=
EOF
```

### Explicación técnica:
* `cat << 'EOF' > .env ... EOF`: Redirecciona un bloque de texto multi-línea (*Heredoc*) directamente hacia un nuevo archivo llamado `.env` en la raíz del proyecto.
* `JIRA_BASE_URL`: Dominio corporativo de la instancia de Atlassian Jira Cloud (`toyota-sie.atlassian.net`).
* `JIRA_EMAIL`: Cuenta de correo autorizada en Atlassian para la emisión de solicitudes a la API REST.
* `JIRA_API_TOKEN`: Token de autenticación Basic encriptado generado en la consola de seguridad de Atlassian.
* `JIRA_PROJECT_KEY`: Identificador del proyecto destino (`PROJ`) en Jira Service Management donde se registran los incidentes y cambios.
* `JIRA_ISSUE_TYPE`: Parámetro opcional para forzar un tipo de issue específico; vacío activa la autodetección inteligente de ITIL en `JiraService.py`.

---

## 5. Orquestación y Despliegue Multi-Contenedor (Docker Compose)

Inicia el proceso de construcción y puesta en marcha de los servicios del sistema:

```bash
sudo docker compose up -d --build
```

### Explicación técnica:
* `sudo docker compose`: Invoca al orquestador de contenedores utilizando las definiciones de servicios, redes y volúmenes de `docker-compose.yml`.
* `up`: Analiza el manifiesto, resuelve las dependencias de arranque (`depends_on`), crea la red bridge `toyotasie_default`, aprovisiona los volúmenes persistentes y arranca los contenedores.
* `-d` (*Detached*): Ejecuta los contenedores en segundo plano, liberando la consola de terminal para continuar trabajando sin interrumpir los servicios.
* `--build`: Fuerza la compilación limpia de las imágenes Docker locales (`./frontend` con Node/Vite y `./backend` con Python Flask), garantizando que cualquier cambio de código se incorpore a la imagen final.

---

## 6. Verificación del Estado de los Contenedores

Para comprobar que toda la arquitectura está operativa y con pruebas de salud (*healthchecks*) superadas, ejecuta:

```bash
sudo docker compose ps
```

### Mapa de Contenedores Activos:
1. `toyota_mysql_master`: Base de datos transaccional principal en puerto `3310:3306` (Estado: `Healthy`).
2. `toyota_mysql_slave`: Base de datos de solo lectura y réplica GTID en puerto `3311:3306` (Estado: `Healthy`).
3. `toyota_redis`: Almacén de datos en memoria para caché distribuido de la API en puerto `6379:6379` (Estado: `Healthy`).
4. `toyota_repl_init`: Script transitorio de configuración de réplica Master-Slave (Estado: `Exited (0)` — ejecución exitosa).
5. `toyota_backend`: API REST en Python Flask conectada a Jira y a los dos nodos de MySQL en puerto `5000:5000` (Estado: `Up`).
6. `toyota_frontend`: Aplicación web React compilada y servida mediante Nginx en puerto `8080:80` (Estado: `Up`).
7. `toyota_prometheus`: Motor de monitoreo y recolección de series temporales en puerto `9091:9090` (Estado: `Up`).
8. `toyota_grafana`: Servidor de tableros de métricas en puerto `3001:3000` (Estado: `Up`).
9. `toyota_node_exporter`, `toyota_cadvisor`, `toyota_mysql_master_exporter`, `toyota_mysql_slave_exporter`, `toyota_redis_exporter`: Agentes de métricas de telemetría de hardware y contenedores.

---

## 7. Verificación de Accesos en Producción

Una vez desplegados los contenedores, los servicios quedan disponibles a través de la red:

| Servicio | URL / Host | Credenciales por Defecto |
| :--- | :--- | :--- |
| **Aplicación Web Oficial** | `http://158.23.20.45:8080` | `soporte_ti` / `Toyota2026!` o `admin_gerente` / `Toyota2026!` |
| **Tablero Grafana** | `http://158.23.20.45:3001` | Usuario: `admin` / Clave: `admin` |
| **Métricas Prometheus** | `http://158.23.20.45:9091` | Acceso directo / Targets de observabilidad |
| **MySQL Master (Workbench)** | `158.23.20.45:3310` | Usuario: `root` / Clave: `123456` |
| **MySQL Slave (Workbench)** | `158.23.20.45:3311` | Usuario: `root` / Clave: `123456` |

---

## 8. Comandos Útiles para Administración y Mantenimiento

Comandos comunes para operar los contenedores en el servidor:

* **Visualizar registros en vivo del backend:**
  ```bash
  sudo docker compose logs -f backend
  ```
* **Verificar sincronización de la réplica MySQL:**
  ```bash
  sudo docker exec -it toyota_mysql_slave mysql -uroot -p123456 -e "SHOW REPLICA STATUS\G"
  ```
* **Reiniciar un contenedor específico (ejemplo tras actualizar `.env`):**
  ```bash
  sudo docker compose up -d --force-recreate backend
  ```
* **Detener todos los servicios:**
  ```bash
  sudo docker compose down
  ```
* **Detener la máquina virtual al finalizar para no consumir créditos de estudiante:**
  *(Se ejecuta en PowerShell personal)*
  ```powershell
  # O desde el portal de Azure haciendo clic en el botón "Detener (Desasignar)"
  ```
