import React, { useState, useEffect } from 'react';
import Login from './Login';
import Dashboard from './Dashboard';
import Ventas from './Ventas';
import Inventario from './Inventario';
import Taller from './Taller';
import Auditoria from './Auditoria';
import AreaTI from './AreaTI';
import ServiceDeskFlotante from './ServiceDeskFlotante';
import './estilos.css';

/* Componente principal de la aplicacion y controlador de rutas por rol */
export default function App() {
  /* Estado que almacena la sesion del usuario actual */
  const [usuario, setUsuario] = useState(null);
  /* Estado para el modulo actualmente visible en pantalla */
  const [moduloActivo, setModuloActivo] = useState('dashboard');
  /* Estado para alternar el menu lateral en pantallas pequeñas o moviles */
  const [menuMovilAbierto, setMenuMovilAbierto] = useState(false);
  /* Contador para refrescar AreaTI cuando se crea un ticket desde el boton flotante */
  const [refrescoTI, setRefrescoTI] = useState(0);

  /* Recuperar sesion guardada en localStorage si existe */
  useEffect(() => {
    const sesionGuardada = localStorage.getItem('toyota_sesion');
    if (sesionGuardada) {
      try {
        const user = JSON.parse(sesionGuardada);
        setUsuario(user);
        if (user.rol === 'Operador') {
          setModuloActivo('ventas');
        } else if (user.rol === 'TI') {
          setModuloActivo('area-ti');
        }
      } catch {
        localStorage.removeItem('toyota_sesion');
      }
    }
  }, []);

  /* Manejar el inicio de sesion exitoso */
  const manejarLogin = (datosUsuario) => {
    setUsuario(datosUsuario);
    localStorage.setItem('toyota_sesion', JSON.stringify(datosUsuario));
    if (datosUsuario.rol === 'Operador') {
      setModuloActivo('ventas');
    } else if (datosUsuario.rol === 'TI') {
      setModuloActivo('area-ti');
    } else {
      setModuloActivo('dashboard');
    }
  };

  /* Cerrar sesion del usuario y limpiar almacenamiento local */
  const manejarCerrarSesion = () => {
    setUsuario(null);
    localStorage.removeItem('toyota_sesion');
    setModuloActivo('dashboard');
    setMenuMovilAbierto(false);
  };

  /* Cambiar de modulo activo y cerrar menu movil en resoluciones reducidas */
  const cambiarModulo = (nuevoModulo) => {
    setModuloActivo(nuevoModulo);
    setMenuMovilAbierto(false);
  };

  /* Si no hay sesion activa, mostrar la pantalla de Login */
  if (!usuario) {
    return <Login onLoginExitoso={manejarLogin} />;
  }

  /* Determinar roles para accesos segun perfil RBAC */
  const esGerente = usuario.rol === 'Gerente';
  const esTI = usuario.rol === 'TI';

  return (
    <div className="layout-principal">
      {/* Fondo oscuro para cerrar menu lateral en dispositivos moviles */}
      {menuMovilAbierto && (
        <div
          className="overlay-movil"
          onClick={() => setMenuMovilAbierto(false)}
        />
      )}

      {/* Barra lateral de navegacion con posicion fija y soporte responsive */}
      <aside className={`barra-lateral no-imprimir ${menuMovilAbierto ? 'abierta-movil' : ''}`}>
        <div className="logo-contenedor">
          <div className="logo-insignia">TOYOTA</div>
          <div className="logo-texto">
            <h2>SIG-Toyota</h2>
            <p>Arequipa Concesionario</p>
          </div>
          {/* Boton para cerrar menu en vista movil */}
          <button
            type="button"
            className="btn-cerrar-menu-movil"
            onClick={() => setMenuMovilAbierto(false)}
          >
            ✕
          </button>
        </div>

        {/* Menu lateral de navegacion segun perfil de usuario */}
        <ul className="navegacion-lista">
          {/* El Dashboard solo es visible para Gerencia */}
          {esGerente && (
            <li>
              <button
                className={`nav-item-btn ${moduloActivo === 'dashboard' ? 'activo' : ''}`}
                onClick={() => cambiarModulo('dashboard')}
              >
                📊 Dirección General (KPIs)
              </button>
            </li>
          )}

          {!esTI && (
            <>
              <li>
                <button
                  className={`nav-item-btn ${moduloActivo === 'ventas' ? 'activo' : ''}`}
                  onClick={() => cambiarModulo('ventas')}
                >
                  💼 Marketing y Ventas
                </button>
              </li>

              <li>
                <button
                  className={`nav-item-btn ${moduloActivo === 'inventario' ? 'activo' : ''}`}
                  onClick={() => cambiarModulo('inventario')}
                >
                  📦 Logística y Almacén
                </button>
              </li>

              <li>
                <button
                  className={`nav-item-btn ${moduloActivo === 'taller' ? 'activo' : ''}`}
                  onClick={() => cambiarModulo('taller')}
                >
                  🔧 Operaciones y Taller
                </button>
              </li>
            </>
          )}

          {/* Area de TI y Service Desk visible para TI y Gerente */}
          {(esGerente || esTI) && (
            <li>
              <button
                className={`nav-item-btn ${moduloActivo === 'area-ti' ? 'activo' : ''}`}
                onClick={() => cambiarModulo('area-ti')}
              >
                🖥️ Área de TI (Service Desk)
              </button>
            </li>
          )}

          {/* Modulo de auditoria visible para Gerente y TI (ISO 27001) */}
          {(esGerente || esTI) && (
            <li>
              <button
                className={`nav-item-btn ${moduloActivo === 'auditoria' ? 'activo' : ''}`}
                onClick={() => cambiarModulo('auditoria')}
              >
                🛡️ Seguridad y Auditoría
              </button>
            </li>
          )}
        </ul>

        {/* Informacion de usuario y primer boton de cierre de sesion al pie de la barra lateral */}
        <div className="perfil-pie">
          <div className="usuario-info">
            <strong>{usuario.nombre_completo}</strong>
            <span>Rol: {usuario.rol}</span>
          </div>
          <button onClick={manejarCerrarSesion} className="btn-cerrar-sesion" title="Cerrar sesión">
            🚪 Cerrar Sesión
          </button>
        </div>
      </aside>

      {/* Area donde se renderiza el contenido del modulo seleccionado */}
      <main className="area-contenido">
        {/* Barra superior con titulo, boton hamburguesa y segundo boton visible de cerrar sesion */}
        <header className="barra-superior no-imprimir">
          <div className="barra-superior-izquierda">
            <button
              type="button"
              className="btn-hamburguesa-movil"
              onClick={() => setMenuMovilAbierto(!menuMovilAbierto)}
              title="Abrir menú"
            >
              ☰
            </button>
            <h1>
              {moduloActivo === 'dashboard' && 'Panel de Dirección y Gestión Estratégica'}
              {moduloActivo === 'ventas' && 'Módulo de Marketing, Ventas y Cotizaciones'}
              {moduloActivo === 'inventario' && 'Módulo de Distribución, Logística y Almacén'}
              {moduloActivo === 'taller' && 'Módulo de Operaciones Técnicas y Mantenimiento'}
              {moduloActivo === 'area-ti' && 'Área de TI — Mesa de Ayuda (Service Desk) y Cambios'}
              {moduloActivo === 'auditoria' && 'Módulo de Seguridad de Información (ISO 27001)'}
            </h1>
          </div>

          {/* Acciones de usuario en cabecera: SIEMPRE visible en todas las pantallas */}
          <div className="usuario-acciones-top">
            <span className="badge badge-neutro usuario-badge-texto">
              👤 <strong>{usuario.nombre_completo}</strong> ({usuario.rol})
            </span>
            <button
              onClick={manejarCerrarSesion}
              className="btn-cerrar-sesion-header"
              title="Cerrar sesión del sistema"
            >
              🚪 Cerrar Sesión
            </button>
          </div>
        </header>

        {/* Renderizado condicional del componente correspondiente */}
        {moduloActivo === 'dashboard' && esGerente && <Dashboard usuario={usuario} />}
        {moduloActivo === 'ventas' && !esTI && <Ventas usuario={usuario} />}
        {moduloActivo === 'inventario' && !esTI && <Inventario usuario={usuario} />}
        {moduloActivo === 'taller' && !esTI && <Taller usuario={usuario} />}
        {moduloActivo === 'area-ti' && (esGerente || esTI) && <AreaTI usuario={usuario} refrescoExterno={refrescoTI} />}
        {moduloActivo === 'auditoria' && (esGerente || esTI) && <Auditoria usuario={usuario} />}
      </main>

      {/* Boton flotante inferior derecho de Service Desk para enviar incidentes y solicitudes */}
      <ServiceDeskFlotante
        usuario={usuario}
        onTicketCreado={() => setRefrescoTI((n) => n + 1)}
      />
    </div>
  );
}
