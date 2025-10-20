# Configuración de Roles de Usuario en CorpChat

**Última actualización**: 15 Octubre 2025

---

## 🎯 **Comportamiento Actual de Roles**

### **Primer Usuario (Tú)**
- ✅ **Rol**: ADMIN
- ✅ **Acceso**: Completo (usuarios, configuraciones, etc.)
- ✅ **Razón**: El primer usuario siempre es ADMIN por diseño de Open WebUI

### **Usuarios Siguientes**
- ✅ **Rol**: PENDING (requiere aprobación)
- ✅ **Acceso**: Limitado hasta aprobación del admin
- ✅ **Seguridad**: Control total sobre quién puede acceder

---

## 🔧 **Configuración Implementada**

### **Variables de Entorno Configuradas:**
```yaml
DEFAULT_USER_ROLE: "pending"  # Los nuevos usuarios requieren aprobación
ENABLE_OAUTH_SIGNUP: "true"   # Permite registro via Google OAuth
ENABLE_SIGNUP: "false"        # Deshabilita registro local
ENABLE_LOGIN_FORM: "false"    # Deshabilita login local
```

---

## 👥 **Gestión de Usuarios desde la Consola Admin**

### **Como ADMIN, puedes:**

1. **Ver usuarios pendientes**:
   - Ir a "Usuarios" → "Vista General"
   - Ver usuarios con rol "PENDING"

2. **Aprobar usuarios**:
   - Clic en el icono de lápiz del usuario
   - Cambiar rol de "PENDING" a "USER"

3. **Asignar roles específicos**:
   - **USER**: Usuario estándar (acceso completo a chat)
   - **ADMIN**: Administrador (gestión de usuarios y configuraciones)
   - **PENDING**: Esperando aprobación

---

## 🛡️ **Flujo de Seguridad Implementado**

### **Registro de Nuevos Usuarios:**
1. **Usuario hace login** con Google OAuth
2. **Sistema crea cuenta** automáticamente
3. **Rol asignado**: PENDING
4. **Acceso**: Limitado hasta aprobación
5. **Admin recibe notificación** (opcional)
6. **Admin aprueba** manualmente desde consola

### **Ventajas de este Flujo:**
- ✅ **Control total** sobre quién accede
- ✅ **No hay usuarios no deseados**
- ✅ **Auditoría completa** de usuarios
- ✅ **Gestión centralizada** por admin

---

## 🔄 **Alternativas de Configuración**

### **Opción A: Aprobación Manual (Actual)**
```yaml
DEFAULT_USER_ROLE: "pending"
```
- **Ventaja**: Máximo control
- **Desventaja**: Requiere aprobación manual

### **Opción B: Acceso Automático**
```yaml
DEFAULT_USER_ROLE: "user"
```
- **Ventaja**: Sin fricción para usuarios
- **Desventaja**: Menos control

### **Opción C: Solo Dominio Corporativo**
```yaml
DEFAULT_USER_ROLE: "user"
OAUTH_GOOGLE_DOMAIN: "summan.com"  # Solo usuarios del dominio
```
- **Ventaja**: Control por dominio + sin fricción
- **Desventaja**: Requiere configuración adicional

---

## 📋 **Recomendaciones**

### **Para Entorno Corporativo:**
1. **Mantener aprobación manual** (configuración actual)
2. **Configurar notificaciones** cuando lleguen usuarios pendientes
3. **Establecer proceso** de aprobación (quién aprueba, cuándo, etc.)

### **Para Entorno Abierto:**
1. **Cambiar a acceso automático** (`DEFAULT_USER_ROLE: "user"`)
2. **Configurar restricciones por dominio** si es necesario
3. **Implementar límites de uso** por usuario

---

## 🚀 **Próximos Pasos**

1. **Probar con usuario de prueba** (crear cuenta con otro email)
2. **Verificar flujo de aprobación** desde consola admin
3. **Configurar notificaciones** (opcional)
4. **Documentar proceso** para el equipo

---

## ❓ **¿Qué prefieres?**

**¿Quieres mantener la configuración actual (aprobación manual) o cambiar a acceso automático?**

- **Mantener actual**: Máximo control, aprobación manual
- **Cambiar a automático**: Sin fricción, acceso inmediato
- **Configurar por dominio**: Solo usuarios de `@summan.com`
