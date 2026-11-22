import React, { useState } from 'react';
import { apiLogin } from './servicios/api';
/* Importacion del logotipo oficial de Toyota */
import toyotaLogo from './assets/ToyotaLogo.jpg';

/* Componente de inicio de sesion y autenticacion */
export default function Login({ onLoginExitoso }) {
  /* Estado para el nombre de usuario ingresado */
  const [username, setUsername] = useState('');
  /* Estado para la clave ingresada */
  const [password, setPassword] = useState('');
  /* Estado para capturar y mostrar mensajes de error */
  const [error, setError] = useState('');
  /* Estado de carga durante la peticion */
  const [cargando, setCargando] = useState(false);

  /* Manejador del envio del formulario de login */
  const manejarSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setCargando(true);
    try {
      /* Llamada al servicio de autenticacion */
      const res = await apiLogin(username, password);
      if (res && res.usuario) {
        /* Notificar al componente padre App sobre el usuario autenticado */
        onLoginExitoso(res.usuario);
      }
    } catch (err) {
      /* Mostrar mensaje puntual en caso de credenciales invalidas */
      setError(err.message || 'Error de conexion o credenciales incorrectas');
    } finally {
      setCargando(false);
    }
  };

  /* Funcion de conveniencia para cargar credenciales de prueba en un clic */
  const cargarCredencialesDemo = (tipoRol) => {
    if (tipoRol === 'Gerente') {
      setUsername('admin_gerente');
      setPassword('Toyota2026!');
    } else {
      setUsername('operador_taller');
      setPassword('Toyota2026!');
    }
    setError('');
  };

  return (
    <div className="login-contenedor">
      <div className="login-tarjeta">
        <div className="login-encabezado">
          {/* Logotipo oficial de Toyota centrado */}
          <div className="login-logo-img-wrapper">
            <img
              src={toyotaLogo}
              alt="Logo Oficial Toyota"
              className="login-logo-img"
            />
          </div>
          <h2>SIG-Toyota</h2>
          <p>Sistema de Información Empresarial — Sede Arequipa</p>
        </div>

        {/* Mostrar mensaje de alerta si ocurrio un error */}
        {error && <div className="mensaje-alerta error">{error}</div>}

        <form onSubmit={manejarSubmit} className="login-form">
          <div className="campo-grupo">
            <label htmlFor="username">Usuario del Sistema</label>
            <input
              id="username"
              type="text"
              placeholder="Ej. admin_gerente o operador_taller"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="campo-grupo">
            <label htmlFor="password">Contraseña</label>
            <input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn btn-primario" disabled={cargando} style={{ width: '100%', marginTop: '0.5rem' }}>
            {cargando ? 'Verificando...' : 'Iniciar Sesión'}
          </button>
        </form>

        {/* Botones de demostracion rapida para la sustentacion */}
        <div className="login-demo-roles">
          <p><strong>Accesos Rápidos para Sustentación:</strong></p>
          <div className="demo-botones-grupo">
            <button
              type="button"
              className="btn-demo"
              onClick={() => cargarCredencialesDemo('Gerente')}
            >
              👤 Rol Gerente
            </button>
            <button
              type="button"
              className="btn-demo"
              onClick={() => cargarCredencialesDemo('Operador')}
            >
              🔧 Rol Operador
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
