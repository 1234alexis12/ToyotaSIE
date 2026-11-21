import React, { useState, useEffect } from 'react';
import { apiObtenerDashboard } from './servicios/api';

/* Componente del modulo de Direccion General y KPIs */
export default function Dashboard({ usuario }) {
  /* Estado que almacena las metricas clave y listas recientes */
  const [datos, setDatos] = useState({
    kpis: {
      totalVendido: 0,
      vehiculosDisponibles: 0,
      repuestosAlerta: 0,
      ordenesActivas: 0
    },
    ventasRecientes: [],
    ordenesRecientes: []
  });

  /* Cargar datos consolidados al montar el componente */
  useEffect(() => {
    cargarMetricas();
  }, []);

  /* Funcion para consultar las metricas del backend o calculo local */
  const cargarMetricas = async () => {
    try {
      const resultado = await apiObtenerDashboard();
      if (resultado && resultado.kpis) {
        setDatos(resultado);
      }
    } catch (error) {
      console.error('Error al cargar datos del dashboard:', error);
    }
  };

  /* Accion para invocar la impresion del reporte gerencial en PDF */
  const imprimirReporte = () => {
    window.print();
  };

  return (
    <div className="vista-interior">
      {/* Membrete formal visible unicamente al imprimir o exportar a PDF */}
      <div className="membrete-impresion">
        <h2>TOYOTA DEL PERÚ — CONCESIONARIO AUTORIZADO AREQUIPA</h2>
        <p>Informe Consolidado de Gestión y Rendimiento Operativo — {new Date().toLocaleDateString('es-PE')}</p>
        <p>Generado por: {usuario?.nombre_completo || 'Gerencia General'}</p>
      </div>

      {/* Barra superior con titulo del modulo y boton de impresion */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>Panel de Control Gerencial</h2>
          <p style={{ color: 'var(--color-texto-muted)', fontSize: '0.9rem' }}>
            Indicadores de rendimiento clave (KPIs) en tiempo real para toma de decisiones
          </p>
        </div>
        <button onClick={imprimirReporte} className="btn btn-imprimir no-imprimir">
          🖨️ Imprimir Reporte / Exportar PDF
        </button>
      </div>

      {/* Grilla con los 4 indicadores clave exigidos en el informe */}
      <div className="grilla-kpis">
        {/* KPI 1: Total facturado en ventas cerradas */}
        <div className="kpi-tarjeta exito">
          <div className="kpi-titulo">Total Ventas Cerradas</div>
          <div className="kpi-valor">${datos.kpis.totalVendido.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
          <div className="kpi-subtexto">Ingresos acumulados en USD</div>
        </div>

        {/* KPI 2: Stock de vehiculos nuevos listos para entrega */}
        <div className="kpi-tarjeta">
          <div className="kpi-titulo">Vehículos en Stock</div>
          <div className="kpi-valor">{datos.kpis.vehiculosDisponibles}</div>
          <div className="kpi-subtexto">Unidades físicas en patio</div>
        </div>

        {/* KPI 3: Alertas de repuestos por debajo del stock de seguridad */}
        <div className="kpi-tarjeta alerta">
          <div className="kpi-titulo">Repuestos en Alerta</div>
          <div className="kpi-valor">{datos.kpis.repuestosAlerta}</div>
          <div className="kpi-subtexto">Ítems por debajo del stock mínimo</div>
        </div>

        {/* KPI 4: Carga operativa actual en taller de servicio */}
        <div className="kpi-tarjeta proceso">
          <div className="kpi-titulo">Órdenes en Taller</div>
          <div className="kpi-valor">{datos.kpis.ordenesActivas}</div>
          <div className="kpi-subtexto">Bahías y mantenimientos activos</div>
        </div>
      </div>

      {/* Tabla resumen de ultimas ventas registradas */}
      <div className="tarjeta">
        <div className="tarjeta-encabezado">
          <h3>Últimas Transacciones Comerciales</h3>
          <span className="badge badge-neutro">Marketing y Ventas</span>
        </div>
        <div className="tabla-contenedor">
          <table>
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Cliente</th>
                <th>Modelo de Vehículo</th>
                <th>Monto (USD)</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {datos.ventasRecientes.map((venta) => (
                <tr key={venta.id_venta}>
                  <td>{venta.fecha}</td>
                  <td>{venta.cliente_nombre}</td>
                  <td><strong>{venta.vehiculo_nombre}</strong></td>
                  <td>${Number(venta.precio_total).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  <td>
                    <span className={`badge ${venta.estado === 'Vendido' ? 'badge-exito' : venta.estado === 'Cotizado' ? 'badge-proceso' : 'badge-neutro'}`}>
                      {venta.estado}
                    </span>
                  </td>
                </tr>
              ))}
              {datos.ventasRecientes.length === 0 && (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '1rem' }}>No hay ventas registradas</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Tabla resumen del estado operativo del taller */}
      <div className="tarjeta">
        <div className="tarjeta-encabezado">
          <h3>Estado Operativo del Taller Técnico (Posventa)</h3>
          <span className="badge badge-neutro">Producción y Operaciones</span>
        </div>
        <div className="tabla-contenedor">
          <table>
            <thead>
              <tr>
                <th>Fecha Ingreso</th>
                <th>Placa / VIN</th>
                <th>Tipo de Servicio</th>
                <th>Técnico a Cargo</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {datos.ordenesRecientes.map((orden) => (
                <tr key={orden.id_orden}>
                  <td>{orden.fecha_ingreso}</td>
                  <td><strong>{orden.placa_vin}</strong></td>
                  <td>{orden.tipo_servicio}</td>
                  <td>{orden.tecnico}</td>
                  <td>
                    <span className={`badge ${orden.estado === 'Entregado' ? 'badge-exito' : orden.estado === 'En proceso' ? 'badge-proceso' : 'badge-alerta'}`}>
                      {orden.estado}
                    </span>
                  </td>
                </tr>
              ))}
              {datos.ordenesRecientes.length === 0 && (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '1rem' }}>No hay órdenes en taller</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
