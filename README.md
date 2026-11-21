# SIG-Toyota (Sistema de Información de Gestión - Toyota Arequipa)

Sistema integral de gestión empresarial para concesionario autorizado de **Toyota del Perú en Arequipa**, desarrollado para el curso **Sistemas de Información Empresarial**.

## Arquitectura del Proyecto

El sistema está diseñado bajo un enfoque modular desacoplado:
* **Frontend:** React 18 + Vite, componentes nativos HTML, diseño CSS puro (`estilos.css`) con variables personalizables y soporte para reportes imprimibles (`@media print`).
* **Backend:** Python 3 + Flask API REST bajo patrones arquitectónicos **MVC**, **DAO** (Data Access Object), **DTO** (Data Transfer Object) y principios **SOLID**.
* **Base de Datos:** MySQL 8.0 relacional con 6 tablas normalizadas, integridad referencial, índices de optimización y bitácora de auditoría inmutable (ISO 27001).

---

## Módulos Empresariales Implementados

1. **Marketing y Ventas (`Ventas.jsx`):** Emisión de cotizaciones, gestión de prospectos y cierre de ventas de vehículos Toyota con descuento transaccional de inventario.
2. **Distribución, Logística y Almacén (`Inventario.jsx`):** Control de existencias de vehículos (código VIN) y repuestos originales OEM (código SKU), con cálculo automático de stock de seguridad y alertas visuales.
3. **Producción y Operaciones (`Taller.jsx`):** Gestión de órdenes de trabajo (OT), servicio posventa, inspección pre-entrega (PDI), asignación de mecánicos y deducción automática de repuestos consumidos.
4. **Dirección General (`Dashboard.jsx`):** Tablero ejecutivo con 4 indicadores de rendimiento (KPIs), métricas en tiempo real y generación de reportes impresos / PDF.
5. **Seguridad y Auditoría (`Login.jsx`, `Auditoria.jsx`):** Control de acceso basado en roles (**RBAC**: Gerente y Operador) y bitácora de trazabilidad conforme a la norma **ISO/IEC 27001** y la **Ley N.° 29733**.

---

## Estructura del Repositorio

```text
ToyotaSIE/
├── .gitignore
├── README.md
├── frontend/                   # Aplicación Web React + Vite
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx            # Punto de entrada
│       ├── App.jsx             # Navegación y control de sesiones
│       ├── estilos.css         # Hoja de estilos con variables :root
│       ├── Login.jsx           # Autenticación y acceso rápido por rol
│       ├── Dashboard.jsx       # Métricas de Gerencia General y reportes
│       ├── Ventas.jsx          # Gestión comercial y cotizaciones
│       ├── Inventario.jsx      # Control de almacén y stock crítico
│       ├── Taller.jsx          # Taller técnico y posventa
│       ├── Auditoria.jsx       # Trazabilidad de seguridad ISO 27001
│       └── servicios/
│           └── api.js          # Consumo de endpoints y fallback local
├── backend/                    # Servidor Flask REST (Paso 2)
└── database/                   # Scripts MySQL y Replicación (Paso 3)
```

---

## Instrucciones de Ejecución del Frontend

1. Ingresar a la carpeta `frontend/`:
   ```bash
   cd frontend
   ```
2. Instalar dependencias:
   ```bash
   npm install
   ```
3. Iniciar el servidor de desarrollo:
   ```bash
   npm run dev
   ```
4. Abrir en el navegador: `http://localhost:5173`

### Credenciales de Demostración:
* **Gerente:** Usuario `admin_gerente` | Clave: `Toyota2026!` (Acceso a todos los módulos)
* **Operador:** Usuario `operador_taller` | Clave: `Toyota2026!` (Acceso a Ventas, Inventario y Taller)
