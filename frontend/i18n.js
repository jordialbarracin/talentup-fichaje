/* ============================================================
   TalentUP Fichaje — i18n (Internationalization)
   Languages: ES (Spanish), CA (Catalan), EN (English)
   Default: ES
   Stored in localStorage as 'talentup_lang'
   ============================================================ */

(function (global) {
  'use strict';

  // ===== TRANSLATIONS =====
  const translations = {
    es: {
      // App / meta
      'app.title': 'TalentUP Fichaje',
      'app.subtitle': 'Panel de gestión para hostelería',
      'app.version': 'v2.0.0',

      // Login
      'login.email': 'Correo electrónico',
      'login.password': 'Contraseña',
      'login.button': 'Iniciar sesión',
      'login.demo': 'Entrar modo demo',
      'login.help': '¿Necesitas ayuda?',
      'login.docs': 'Documentación',
      'login.error_empty': 'Completa todos los campos',
      'login.loading': 'Iniciando sesión…',
      'login.error_credentials': 'Credenciales incorrectas. Verifica tu email y contraseña.',

      // Demo banner
      'demo.banner': 'Modo demo — los datos mostrados no son reales',

      // Navigation
      'nav.dashboard': 'Dashboard',
      'nav.employees': 'Empleados',
      'nav.calendar': 'Calendario',
      'nav.shifts': 'Turnos',
      'nav.clocking': 'Fichajes',
      'nav.vacations': 'Vacaciones',
      'nav.leave': 'Bajas',
      'nav.reports': 'Informes',
      'nav.settings': 'Configuración',

      // Buttons
      'button.login': 'Iniciar sesión',
      'button.logout': 'Cerrar sesión',
      'button.logout_short': 'Salir',
      'button.save': 'Guardar',
      'button.cancel': 'Cancelar',
      'button.delete': 'Eliminar',
      'button.edit': 'Editar',
      'button.add': 'Añadir',
      'button.assign': 'Asignar',
      'button.approve': 'Aprobar',
      'button.reject': 'Rechazar',
      'button.generate': 'Generar informe',
      'button.export_pdf': 'Exportar PDF',
      'button.export_excel': 'Exportar Excel',
      'button.save_settings': 'Guardar configuración',
      'button.add_employee': 'Añadir empleado',
      'button.create_shift': 'Crear turno',
      'button.new_request': 'Nueva solicitud',
      'button.register_leave': 'Registrar baja',
      'button.scan_nfc': 'Escanear NFC',
      'button.download_qr': 'Descargar QR',
      'button.print_qr': 'Imprimir QR',
      'button.give_discharge': 'Dar alta',
      'button.weekly': 'Semanal',
      'button.monthly': 'Mensual',
      'button.today': 'Hoy',

      // Status
      'status.online': 'Conectado',
      'status.offline': 'Sin conexión',
      'status.demo': 'Demo',
      'status.loading': 'Cargando…',
      'status.ok': 'OK',
      'status.late': 'Tarde',
      'status.incident': 'Incidencia',
      'status.active': 'Activo',
      'status.inactive': 'Inactivo',
      'status.on_vacation': 'Vacaciones',
      'status.on_leave': 'De baja',
      'status.pending': 'Pendiente',
      'status.approved': 'Aprobada',
      'status.rejected': 'Rechazada',
      'status.finished': 'Finalizada',
      'status.active_leave': 'Activa',
      'status.not_available': 'No disponible',

      // Table headers
      'table.name': 'Nombre',
      'table.dni': 'DNI',
      'table.nss': 'N.º SS',
      'table.category': 'Categoría',
      'table.contract': 'Contrato',
      'table.shift': 'Turno',
      'table.pin': 'PIN',
      'table.status': 'Estado',
      'table.actions': 'Acciones',
      'table.action': 'Acción',
      'table.employee': 'Empleado',
      'table.type': 'Tipo',
      'table.time': 'Hora',
      'table.date': 'Fecha',
      'table.from': 'Desde',
      'table.to': 'Hasta',
      'table.days': 'Días',
      'table.start': 'Inicio',
      'table.expected_end': 'Fin previsto',

      // Clock types
      'clock.in': 'Entrada',
      'clock.out': 'Salida',
      'clock.break_start': 'Pausa',
      'clock.break_end': 'Vuelta',
      'clock.history': 'Histórico completo de fichajes',
      'clock.today': 'Fichajes de hoy',

      // Modal
      'modal.confirm_delete': '¿Eliminar este elemento?',
      'modal.confirm_delete_employee': '¿Eliminar este empleado?',
      'modal.confirm_delete_shift': '¿Eliminar este turno?',
      'modal.confirm_delete_holiday': '¿Eliminar este festivo?',
      'modal.confirm_close_leave': '¿Confirmar alta médica?',
      'modal.confirm_save': '¿Guardar cambios?',
      'modal.cancel': 'Cancelar',
      'modal.save': 'Guardar',
      'modal.assign_shift': 'Asignar turno',
      'modal.select_shift': 'Seleccionar turno',
      'modal.no_shift': 'Sin turno (descanso)',
      'modal.reject_request': 'Rechazar solicitud',
      'modal.reject_reason': 'Motivo del rechazo',
      'modal.reject_reason_placeholder': 'Indica el motivo…',
      'modal.reject_reason_required': 'Indica un motivo para el rechazo',

      // Employee modal
      'modal.edit_employee': 'Editar empleado',
      'modal.add_employee': 'Añadir empleado',
      'modal.first_name': 'Nombre',
      'modal.last_name': 'Apellidos',
      'modal.dni_nie': 'DNI / NIE',
      'modal.ssn': 'N.º Seguridad Social',
      'modal.professional_category': 'Categoría profesional',
      'modal.contract_type': 'Tipo de contrato',
      'modal.default_shift': 'Turno habitual',
      'modal.no_shift_option': 'Sin turno',
      'modal.employee_status': 'Estado',
      'modal.pin_label': 'PIN (4 dígitos) — solo si se cambia',
      'modal.pin_placeholder': 'Dejar vacío para mantener el actual',
      'modal.nfc_card': 'Tarjeta NFC (UID)',
      'modal.employee_qr': 'Codigo QR del empleado',
      'modal.select_placeholder': 'Seleccionar…',

      // Contract types
      'contract.IND': 'Indefinido',
      'contract.TEM-OC': 'Temporal obra',
      'contract.TEM-CIR': 'Temporal circunstancias',
      'contract.TEM-INT': 'Interinidad',
      'contract.PAR-IND': 'Tiempo parcial indefinido',
      'contract.PAR-TEMP': 'Tiempo parcial temporal',

      // Shift modal
      'modal.edit_shift': 'Editar turno',
      'modal.create_shift': 'Crear turno',
      'modal.shift_name': 'Nombre del turno',
      'modal.shift_start': 'Hora de inicio',
      'modal.shift_end': 'Hora de fin',
      'modal.shift_type': 'Tipo de turno',
      'modal.tolerance': 'Tolerancia (minutos)',
      'modal.shift_color': 'Color del turno',

      // Shift types
      'shift_type.morning': 'Mañana',
      'shift_type.afternoon': 'Tarde',
      'shift_type.night': 'Noche',
      'shift_type.split': 'Partido',
      'shift_type.rotating': 'Rotativo',
      'shift_type.custom': 'Personalizado',

      // Vacation modal
      'modal.new_vacation': 'Nueva solicitud de vacaciones',
      'modal.start_date': 'Fecha inicio',
      'modal.end_date': 'Fecha fin',
      'modal.vacation_type': 'Tipo',
      'modal.vacation_reason': 'Motivo (opcional)',
      'modal.vacation_reason_placeholder': 'Motivo de la solicitud…',

      // Vacation types
      'vacation.vacation': 'Vacaciones',
      'vacation.personal_leave': 'Permiso personal',
      'vacation.unpaid_leave': 'Permiso no retribuido',

      // Leave modal
      'modal.register_leave': 'Registrar baja médica',
      'modal.leave_type': 'Tipo de baja',
      'modal.expected_end': 'Fin previsto',
      'modal.diagnosis': 'Diagnóstico (opcional)',
      'modal.diagnosis_placeholder': 'Código / descripción',

      // Leave types
      'leave.EC': 'Enfermedad Común',
      'leave.EC_short': 'Enf. Común',
      'leave.ANL': 'Accidente No Laboral',
      'leave.ANL_short': 'Acc. No Laboral',
      'leave.AL': 'Accidente Laboral',
      'leave.AL_short': 'Acc. Laboral',
      'leave.EP': 'Enfermedad Profesional',
      'leave.EP_short': 'Enf. Profesional',
      'leave.MAT': 'Maternidad',
      'leave.PAT': 'Paternidad',

      // Pages - Dashboard
      'page.dashboard.title': 'Dashboard',
      'page.dashboard.subtitle': 'Resumen ejecutivo de actividad',
      'dashboard.active_today': 'Empleados activos hoy',
      'dashboard.clocks_today': 'Fichajes hoy',
      'dashboard.incidents': 'Incidencias pendientes',
      'dashboard.overtime_week': 'Horas extra esta semana',
      'dashboard.no_clock': 'Sin fichar hoy',
      'dashboard.pending_vacations': 'Vacaciones pendientes',
      'dashboard.all_clocked': 'Todos han fichado',
      'dashboard.no_pending': 'Sin solicitudes pendientes',
      'dashboard.no_clocks_today': 'No hay fichajes hoy',
      'dashboard.no_data': 'No hay datos disponibles — servidor no responde',
      'dashboard.more': 'más',

      // Pages - Empleados
      'page.employees.title': 'Empleados',
      'page.employees.subtitle': 'Gestión completa de la plantilla',
      'employees.search_placeholder': 'Buscar nombre, DNI, SS…',
      'employees.filter_all_status': 'Todos los estados',
      'employees.filter_active': 'Activos',
      'employees.filter_inactive': 'Inactivos',
      'employees.filter_on_vacation': 'De vacaciones',
      'employees.filter_on_leave': 'De baja',
      'employees.filter_all_shifts': 'Todos los turnos',
      'employees.no_results': 'No hay empleados que coincidan con los filtros',
      'employees.load_error': 'No se pudieron cargar los empleados — servidor no responde',

      // Pages - Calendario
      'page.calendar.title': 'Calendario',
      'page.calendar.subtitle': 'Vista mensual con turnos, festivos y vacaciones',
      'calendar.loading': 'Cargando calendario…',
      'calendar.load_employees_first': 'Carga empleados primero',
      'calendar.holiday': 'Festivo',
      'calendar.shift': 'Turno',

      // Pages - Turnos
      'page.shifts.title': 'Turnos',
      'page.shifts.subtitle': 'Configuración de turnos laborales',
      'shifts.loading': 'Cargando turnos…',
      'shifts.none': 'No hay turnos configurados',
      'shifts.load_error': 'No se pudieron cargar los turnos — servidor no responde',
      'shifts.tolerance': 'Tolerancia',

      // Pages - Fichajes
      'page.clocking.title': 'Fichajes',
      'page.clocking.subtitle': 'Histórico completo de fichajes',
      'clocking.filter_all_employees': 'Todos los empleados',
      'clocking.filter_all_types': 'Todos los tipos',
      'clocking.filter_all_status': 'Todos los estados',
      'clocking.no_results': 'No hay fichajes que coincidan con los filtros',
      'clocking.load_error': 'No se pudieron cargar los fichajes — servidor no responde',

      // Pages - Vacaciones
      'page.vacations.title': 'Vacaciones y Permisos',
      'page.vacations.subtitle': 'Gestión de solicitudes y calendario',
      'vacations.pending': 'Solicitudes pendientes',
      'vacations.calendar': 'Calendario de vacaciones',
      'vacations.none': 'No hay solicitudes de vacaciones',
      'vacations.no_approved': 'No hay vacaciones aprobadas',
      'vacations.loading': 'Cargando solicitudes…',
      'vacations.load_error': 'No se pudieron cargar las solicitudes — servidor no responde',

      // Pages - Bajas
      'page.leave.title': 'Bajas (IT)',
      'page.leave.subtitle': 'Registro de incapacidad temporal y permisos',
      'leave.filter_all': 'Todas las bajas',
      'leave.filter_active': 'Activas',
      'leave.filter_finished': 'Finalizadas',
      'leave.filter_all_types': 'Todos los tipos',
      'leave.no_results': 'No hay bajas que coincidan con los filtros',
      'leave.loading': 'Cargando bajas…',
      'leave.load_error': 'No se pudieron cargar las bajas — servidor no responde',

      // Pages - Informes
      'page.reports.title': 'Informes',
      'page.reports.subtitle': 'Reportes de horas, absentismo y costes laborales',
      'reports.from': 'Desde',
      'reports.to': 'Hasta',
      'reports.type': 'Tipo de informe',
      'reports.type_hours': 'Horas trabajadas',
      'reports.type_overtime': 'Horas extra',
      'reports.type_absenteeism': 'Absentismo',
      'reports.type_labor_costs': 'Costes laborales',
      'reports.type_inspection': 'Inspección de trabajo',
      'reports.type_payroll': 'Nómina',
      'reports.title_hours': 'Horas por empleado',
      'reports.empty': 'Selecciona un rango de fechas y genera el informe',
      'reports.no_data': 'No hay datos en el período seleccionado',
      'reports.col_regular_hours': 'Horas ordinarias',
      'reports.col_overtime_hours': 'Horas extra',
      'reports.col_total': 'Total',
      'reports.col_absent_days': 'Días ausencia',
      'reports.col_rate': 'Tasa',
      'reports.col_base_salary': 'Salario base',
      'reports.col_complements': 'Complementos',
      'reports.col_overtime_amount': 'Horas extra',
      'reports.col_scheduled': 'Programadas',
      'reports.col_worked': 'Trabajadas',
      'reports.col_holidays': 'Festivos',
      'reports.col_absences': 'Ausencias',
      'reports.col_clock_in': 'Entrada',
      'reports.col_clock_out': 'Salida',
      'reports.col_minutes': 'Minutos',
      'reports.overtime_structural': 'Estructural',
      'reports.overtime_force_majeure': 'Fuerza Mayor',
      'reports.compensation_pending': 'Pendiente',

      // Settings
      'page.settings.title': 'Configuración',
      'page.settings.subtitle': 'Datos del restaurante, convenio y preferencias',
      'settings.tab_restaurant': 'Restaurante',
      'settings.tab_agreement': 'Convenio',
      'settings.tab_calendar': 'Calendario laboral',
      'settings.tab_holidays': 'Festivos',
      'settings.tab_notifications': 'Notificaciones',
      'settings.language': 'Idioma',
      'settings.theme': 'Tema',
      'settings.notifications': 'Notificaciones',

      // Settings - Restaurant
      'settings.restaurant_name': 'Nombre del restaurante',
      'settings.cif': 'CIF / NIF',
      'settings.address': 'Dirección',
      'settings.phone': 'Teléfono',
      'settings.email': 'Email',

      // Settings - Agreement
      'settings.agreement': 'Convenio colectivo',
      'settings.ccaa': 'Comunidad Autónoma',
      'settings.tolerance': 'Tolerancia de fichaje (minutos)',
      'settings.vacation_days': 'Días de vacaciones por año',

      // Settings - Calendar
      'settings.cal_year': 'Año del calendario laboral',
      'settings.weekly_hours': 'Horas semanales ordinarias',
      'settings.work_days': 'Días laborables por semana',
      'settings.work_days_5': 'Lunes a Viernes',
      'settings.work_days_6': 'Lunes a Sábado',
      'settings.work_days_7': 'Todos los días',

      // Settings - Holidays
      'settings.holiday_year': 'Año',
      'settings.holidays_registered': 'Festivos registrados',
      'settings.holiday_date': 'Fecha',
      'settings.holiday_name': 'Nombre',
      'settings.holiday_type': 'Tipo',
      'settings.holiday_name_placeholder': 'Nombre del festivo',
      'settings.holidays.loading': 'Cargando festivos…',
      'settings.holidays.none': 'No hay festivos registrados',
      'settings.holiday_type_national': 'Nacional',
      'settings.holiday_type_regional': 'Autonómico',
      'settings.holiday_type_local': 'Local',

      // Settings - Notifications
      'settings.notif_email': 'Notificaciones por email',
      'settings.notif_email_all': 'Todas las notificaciones',
      'settings.notif_email_important': 'Solo importantes',
      'settings.notif_email_none': 'Ninguna',
      'settings.notif_clock': 'Recordatorio de fichaje',
      'settings.notif_clock_15': '15 minutos después del inicio',
      'settings.notif_clock_30': '30 minutos después del inicio',
      'settings.notif_clock_60': '1 hora después del inicio',
      'settings.notif_clock_0': 'No recordar',
      'settings.notif_vacation': 'Aviso de vacaciones pendientes',
      'settings.notif_vacation_weekly': 'Semanal',
      'settings.notif_vacation_monthly': 'Mensual',
      'settings.notif_vacation_never': 'Nunca',

      // CCAA
      'ccaa.select': 'Seleccionar…',
      'ccaa.andalucia': 'Andalucía',
      'ccaa.aragon': 'Aragón',
      'ccaa.asturias': 'Asturias',
      'ccaa.baleares': 'Baleares',
      'ccaa.canarias': 'Canarias',
      'ccaa.cantabria': 'Cantabria',
      'ccaa.castilla_mancha': 'Castilla-La Mancha',
      'ccaa.castilla_leon': 'Castilla y León',
      'ccaa.catalunya': 'Cataluña',
      'ccaa.extremadura': 'Extremadura',
      'ccaa.galicia': 'Galicia',
      'ccaa.madrid': 'Comunidad de Madrid',
      'ccaa.murcia': 'Región de Murcia',
      'ccaa.navarra': 'Navarra',
      'ccaa.pais_vasco': 'País Vasco',
      'ccaa.rioja': 'La Rioja',
      'ccaa.valencia': 'Comunidad Valenciana',

      // Toast messages
      'toast.employee_deleted': 'Empleado eliminado correctamente',
      'toast.employee_delete_error': 'Error al eliminar el empleado',
      'toast.employee_created': 'Empleado creado',
      'toast.employee_updated': 'Empleado actualizado',
      'toast.employee_save_error': 'Error al guardar el empleado',
      'toast.name_required': 'El nombre es obligatorio',
      'toast.shift_assigned': 'Turno asignado correctamente',
      'toast.shift_assign_error': 'Error al asignar turno',
      'toast.shift_deleted': 'Turno eliminado correctamente',
      'toast.shift_delete_error': 'Error al eliminar el turno',
      'toast.shift_created': 'Turno creado',
      'toast.shift_updated': 'Turno actualizado',
      'toast.shift_save_error': 'Error al guardar el turno',
      'toast.fields_required': 'Completa todos los campos',
      'toast.fields_required_some': 'Completa los campos obligatorios',
      'toast.vacation_approved': 'Vacaciones aprobadas',
      'toast.vacation_approve_error': 'Error al aprobar',
      'toast.vacation_rejected': 'Vacaciones rechazadas',
      'toast.vacation_reject_error': 'Error al rechazar',
      'toast.vacation_created': 'Solicitud creada',
      'toast.vacation_create_error': 'Error al crear la solicitud',
      'toast.leave_closed': 'Baja cerrada correctamente',
      'toast.leave_close_error': 'Error al cerrar la baja',
      'toast.leave_registered': 'Baja registrada',
      'toast.leave_register_error': 'Error al registrar la baja',
      'toast.settings_saved': 'Configuración guardada correctamente',
      'toast.settings_save_error': 'Error al guardar la configuración',
      'toast.holiday_added': 'Festivo añadido',
      'toast.holiday_add_error': 'Error al añadir festivo',
      'toast.holiday_deleted': 'Festivo eliminado',
      'toast.holiday_delete_error': 'Error al eliminar',
      'toast.holiday_fields_required': 'Completa fecha y nombre del festivo',
      'toast.report_downloaded': 'Informe descargado correctamente',
      'toast.report_download_error': 'Error al descargar el informe',
      'toast.pin_encrypted': 'El PIN está cifrado y no puede mostrarse',
      'toast.pin_load_error': 'No se pudo cargar el PIN',
      'toast.day_detail': 'Detalle del día — próximamente',
      'toast.qr_generate_first': 'Genera primero el codigo QR',
      'toast.qr_downloaded': 'QR descargado',
      'toast.qr_load_error': 'Cargando libreria QR...',
      'toast.qr_generate_error': 'Error al generar QR',
      'toast.popup_required': 'Permite ventanas emergentes para imprimir',

      // NFC
      'nfc.approach': 'Acerca la tarjeta NFC al dispositivo...',
      'nfc.read_success': 'Tarjeta NFC leida correctamente',
      'nfc.read_error': 'Error al leer la tarjeta. Intentalo de nuevo.',
      'nfc.scan_error': 'Error al iniciar el escaner: ',
      'nfc.not_available': 'Web NFC no esta disponible en este navegador. Introduce el UID manualmente. El UID suele estar impreso en la tarjeta o puedes leerlo con una app NFC.',

      // Language selector
      'lang.label': 'Idioma',

      // Misc
      'misc.documentation_arrow': 'Documentación →',
      'misc.select_placeholder': 'Seleccionar…'
    },

    ca: {
      // App / meta
      'app.title': 'TalentUP Fichaje',
      'app.subtitle': 'Panell de gestió per a hostaleria',
      'app.version': 'v2.0.0',

      // Login
      'login.email': 'Correu electrònic',
      'login.password': 'Contrasenya',
      'login.button': 'Iniciar sessió',
      'login.demo': 'Entrar en mode demo',
      'login.help': 'Necessites ajuda?',
      'login.docs': 'Documentació',
      'login.error_empty': 'Completa tots els camps',
      'login.loading': 'Iniciant sessió…',
      'login.error_credentials': 'Credencials incorrectes. Verifica el teu correu i contrasenya.',

      // Demo banner
      'demo.banner': 'Mode demo — les dades mostrades no són reals',

      // Navigation
      'nav.dashboard': 'Tauler',
      'nav.employees': 'Empleats',
      'nav.calendar': 'Calendari',
      'nav.shifts': 'Torns',
      'nav.clocking': 'Fitxatges',
      'nav.vacations': 'Vacances',
      'nav.leave': 'Baixes',
      'nav.reports': 'Informes',
      'nav.settings': 'Configuració',

      // Buttons
      'button.login': 'Iniciar sessió',
      'button.logout': 'Tancar sessió',
      'button.logout_short': 'Sortir',
      'button.save': 'Desar',
      'button.cancel': 'Cancel·lar',
      'button.delete': 'Eliminar',
      'button.edit': 'Editar',
      'button.add': 'Afegir',
      'button.assign': 'Assignar',
      'button.approve': 'Aprovar',
      'button.reject': 'Rebutjar',
      'button.generate': 'Generar informe',
      'button.export_pdf': 'Exportar PDF',
      'button.export_excel': 'Exportar Excel',
      'button.save_settings': 'Desar configuració',
      'button.add_employee': 'Afegir empleat',
      'button.create_shift': 'Crear torn',
      'button.new_request': 'Nova sol·licitud',
      'button.register_leave': 'Registrar baixa',
      'button.scan_nfc': 'Escanejar NFC',
      'button.download_qr': 'Descarregar QR',
      'button.print_qr': 'Imprimir QR',
      'button.give_discharge': 'Donar alta',
      'button.weekly': 'Setmanal',
      'button.monthly': 'Mensual',
      'button.today': 'Avui',

      // Status
      'status.online': 'Connectat',
      'status.offline': 'Sense connexió',
      'status.demo': 'Demo',
      'status.loading': 'Carregant…',
      'status.ok': 'OK',
      'status.late': 'Tard',
      'status.incident': 'Incidència',
      'status.active': 'Actiu',
      'status.inactive': 'Inactiu',
      'status.on_vacation': 'Vacances',
      'status.on_leave': 'De baixa',
      'status.pending': 'Pendent',
      'status.approved': 'Aprovada',
      'status.rejected': 'Rebutjada',
      'status.finished': 'Finalitzada',
      'status.active_leave': 'Activa',
      'status.not_available': 'No disponible',

      // Table headers
      'table.name': 'Nom',
      'table.dni': 'DNI',
      'table.nss': 'N.º SS',
      'table.category': 'Categoria',
      'table.contract': 'Contracte',
      'table.shift': 'Torn',
      'table.pin': 'PIN',
      'table.status': 'Estat',
      'table.actions': 'Accions',
      'table.action': 'Acció',
      'table.employee': 'Empleat',
      'table.type': 'Tipus',
      'table.time': 'Hora',
      'table.date': 'Data',
      'table.from': 'Des de',
      'table.to': 'Fins a',
      'table.days': 'Dies',
      'table.start': 'Inici',
      'table.expected_end': 'Fi previst',

      // Clock types
      'clock.in': 'Entrada',
      'clock.out': 'Sortida',
      'clock.break_start': 'Pausa',
      'clock.break_end': 'Tornada',
      'clock.history': 'Històric complet de fitxatges',
      'clock.today': 'Fitxatges d\'avui',

      // Modal
      'modal.confirm_delete': '¿Eliminar aquest element?',
      'modal.confirm_delete_employee': '¿Eliminar aquest empleat?',
      'modal.confirm_delete_shift': '¿Eliminar aquest torn?',
      'modal.confirm_delete_holiday': '¿Eliminar aquesta festivitat?',
      'modal.confirm_close_leave': '¿Confirmar alta mèdica?',
      'modal.confirm_save': '¿Desar canvis?',
      'modal.cancel': 'Cancel·lar',
      'modal.save': 'Desar',
      'modal.assign_shift': 'Assignar torn',
      'modal.select_shift': 'Seleccionar torn',
      'modal.no_shift': 'Sense torn (descans)',
      'modal.reject_request': 'Rebutjar sol·licitud',
      'modal.reject_reason': 'Motiu del rebuig',
      'modal.reject_reason_placeholder': 'Indica el motiu…',
      'modal.reject_reason_required': 'Indica un motiu per al rebuig',

      // Employee modal
      'modal.edit_employee': 'Editar empleat',
      'modal.add_employee': 'Afegir empleat',
      'modal.first_name': 'Nom',
      'modal.last_name': 'Cognoms',
      'modal.dni_nie': 'DNI / NIE',
      'modal.ssn': 'N.º Seguretat Social',
      'modal.professional_category': 'Categoria professional',
      'modal.contract_type': 'Tipus de contracte',
      'modal.default_shift': 'Torn habitual',
      'modal.no_shift_option': 'Sense torn',
      'modal.employee_status': 'Estat',
      'modal.pin_label': 'PIN (4 dígits) — només si es canvia',
      'modal.pin_placeholder': 'Deixar buit per mantenir l\'actual',
      'modal.nfc_card': 'Targeta NFC (UID)',
      'modal.employee_qr': 'Codi QR de l\'empleat',
      'modal.select_placeholder': 'Seleccionar…',

      // Contract types
      'contract.IND': 'Indefinit',
      'contract.TEM-OC': 'Temporal obra',
      'contract.TEM-CIR': 'Temporal circumstàncies',
      'contract.TEM-INT': 'Interinitat',
      'contract.PAR-IND': 'Temps parcial indefinit',
      'contract.PAR-TEMP': 'Temps parcial temporal',

      // Shift modal
      'modal.edit_shift': 'Editar torn',
      'modal.create_shift': 'Crear torn',
      'modal.shift_name': 'Nom del torn',
      'modal.shift_start': 'Hora d\'inici',
      'modal.shift_end': 'Hora de fi',
      'modal.shift_type': 'Tipus de torn',
      'modal.tolerance': 'Tolerància (minuts)',
      'modal.shift_color': 'Color del torn',

      // Shift types
      'shift_type.morning': 'Matí',
      'shift_type.afternoon': 'Tarda',
      'shift_type.night': 'Nit',
      'shift_type.split': 'Partit',
      'shift_type.rotating': 'Rotatiu',
      'shift_type.custom': 'Personalitzat',

      // Vacation modal
      'modal.new_vacation': 'Nova sol·licitud de vacances',
      'modal.start_date': 'Data d\'inici',
      'modal.end_date': 'Data de fi',
      'modal.vacation_type': 'Tipus',
      'modal.vacation_reason': 'Motiu (opcional)',
      'modal.vacation_reason_placeholder': 'Motiu de la sol·licitud…',

      // Vacation types
      'vacation.vacation': 'Vacances',
      'vacation.personal_leave': 'Permís personal',
      'vacation.unpaid_leave': 'Permís no retribuït',

      // Leave modal
      'modal.register_leave': 'Registrar baixa mèdica',
      'modal.leave_type': 'Tipus de baixa',
      'modal.expected_end': 'Fi previst',
      'modal.diagnosis': 'Diagnòstic (opcional)',
      'modal.diagnosis_placeholder': 'Codi / descripció',

      // Leave types
      'leave.EC': 'Malaltia Comuna',
      'leave.EC_short': 'Mal. Comuna',
      'leave.ANL': 'Accident No Laboral',
      'leave.ANL_short': 'Acc. No Laboral',
      'leave.AL': 'Accident Laboral',
      'leave.AL_short': 'Acc. Laboral',
      'leave.EP': 'Malaltia Professional',
      'leave.EP_short': 'Mal. Professional',
      'leave.MAT': 'Maternitat',
      'leave.PAT': 'Paternitat',

      // Pages - Dashboard
      'page.dashboard.title': 'Tauler',
      'page.dashboard.subtitle': 'Resum executiu d\'activitat',
      'dashboard.active_today': 'Empleats actius avui',
      'dashboard.clocks_today': 'Fitxatges avui',
      'dashboard.incidents': 'Incidències pendents',
      'dashboard.overtime_week': 'Hores extra aquesta setmana',
      'dashboard.no_clock': 'Sense fitxar avui',
      'dashboard.pending_vacations': 'Vacances pendents',
      'dashboard.all_clocked': 'Tots han fitxat',
      'dashboard.no_pending': 'Sense sol·licituds pendents',
      'dashboard.no_clocks_today': 'No hi ha fitxatges avui',
      'dashboard.no_data': 'No hi ha dades disponibles — el servidor no respon',
      'dashboard.more': 'més',

      // Pages - Empleados
      'page.employees.title': 'Empleats',
      'page.employees.subtitle': 'Gestió completa de la plantilla',
      'employees.search_placeholder': 'Cercar nom, DNI, SS…',
      'employees.filter_all_status': 'Tots els estats',
      'employees.filter_active': 'Actius',
      'employees.filter_inactive': 'Inactius',
      'employees.filter_on_vacation': 'De vacances',
      'employees.filter_on_leave': 'De baixa',
      'employees.filter_all_shifts': 'Tots els torns',
      'employees.no_results': 'No hi ha empleats que coincideixin amb els filtres',
      'employees.load_error': 'No s\'han pogut carregar els empleats — el servidor no respon',

      // Pages - Calendario
      'page.calendar.title': 'Calendari',
      'page.calendar.subtitle': 'Vista mensual amb torns, festius i vacances',
      'calendar.loading': 'Carregant calendari…',
      'calendar.load_employees_first': 'Carrega empleats primer',
      'calendar.holiday': 'Festiu',
      'calendar.shift': 'Torn',

      // Pages - Turnos
      'page.shifts.title': 'Torns',
      'page.shifts.subtitle': 'Configuració de torns laborals',
      'shifts.loading': 'Carregant torns…',
      'shifts.none': 'No hi ha torns configurats',
      'shifts.load_error': 'No s\'han pogut carregar els torns — el servidor no respon',
      'shifts.tolerance': 'Tolerància',

      // Pages - Fichajes
      'page.clocking.title': 'Fitxatges',
      'page.clocking.subtitle': 'Històric complet de fitxatges',
      'clocking.filter_all_employees': 'Tots els empleats',
      'clocking.filter_all_types': 'Tots els tipus',
      'clocking.filter_all_status': 'Tots els estats',
      'clocking.no_results': 'No hi ha fitxatges que coincideixin amb els filtres',
      'clocking.load_error': 'No s\'han pogut carregar els fitxatges — el servidor no respon',

      // Pages - Vacaciones
      'page.vacations.title': 'Vacances i Permisos',
      'page.vacations.subtitle': 'Gestió de sol·licituds i calendari',
      'vacations.pending': 'Sol·licituds pendents',
      'vacations.calendar': 'Calendari de vacances',
      'vacations.none': 'No hi ha sol·licituds de vacances',
      'vacations.no_approved': 'No hi ha vacances aprovades',
      'vacations.loading': 'Carregant sol·licituds…',
      'vacations.load_error': 'No s\'han pogut carregar les sol·licituds — el servidor no respon',

      // Pages - Bajas
      'page.leave.title': 'Baixes (IT)',
      'page.leave.subtitle': 'Registre d\'incapacitat temporal i permisos',
      'leave.filter_all': 'Totes les baixes',
      'leave.filter_active': 'Actives',
      'leave.filter_finished': 'Finalitzades',
      'leave.filter_all_types': 'Tots els tipus',
      'leave.no_results': 'No hi ha baixes que coincideixin amb els filtres',
      'leave.loading': 'Carregant baixes…',
      'leave.load_error': 'No s\'han pogut carregar les baixes — el servidor no respon',

      // Pages - Informes
      'page.reports.title': 'Informes',
      'page.reports.subtitle': 'Informes d\'hores, absentisme i costos laborals',
      'reports.from': 'Des de',
      'reports.to': 'Fins a',
      'reports.type': 'Tipus d\'informe',
      'reports.type_hours': 'Hores treballades',
      'reports.type_overtime': 'Hores extra',
      'reports.type_absenteeism': 'Absentisme',
      'reports.type_labor_costs': 'Costos laborals',
      'reports.type_inspection': 'Inspecció de treball',
      'reports.type_payroll': 'Nòmina',
      'reports.title_hours': 'Hores per empleat',
      'reports.empty': 'Selecciona un rang de dates i genera l\'informe',
      'reports.no_data': 'No hi ha dades en el període seleccionat',
      'reports.col_regular_hours': 'Hores ordinàries',
      'reports.col_overtime_hours': 'Hores extra',
      'reports.col_total': 'Total',
      'reports.col_absent_days': 'Dies d\'absència',
      'reports.col_rate': 'Taxa',
      'reports.col_base_salary': 'Salari base',
      'reports.col_complements': 'Complements',
      'reports.col_overtime_amount': 'Hores extra',
      'reports.col_scheduled': 'Programades',
      'reports.col_worked': 'Treballades',
      'reports.col_holidays': 'Festius',
      'reports.col_absences': 'Absències',
      'reports.col_clock_in': 'Entrada',
      'reports.col_clock_out': 'Sortida',
      'reports.col_minutes': 'Minuts',
      'reports.overtime_structural': 'Estructural',
      'reports.overtime_force_majeure': 'Força Major',
      'reports.compensation_pending': 'Pendent',

      // Settings
      'page.settings.title': 'Configuració',
      'page.settings.subtitle': 'Dades del restaurant, conveni i preferències',
      'settings.tab_restaurant': 'Restaurant',
      'settings.tab_agreement': 'Conveni',
      'settings.tab_calendar': 'Calendari laboral',
      'settings.tab_holidays': 'Festius',
      'settings.tab_notifications': 'Notificacions',
      'settings.language': 'Idioma',
      'settings.theme': 'Tema',
      'settings.notifications': 'Notificacions',

      // Settings - Restaurant
      'settings.restaurant_name': 'Nom del restaurant',
      'settings.cif': 'CIF / NIF',
      'settings.address': 'Adreça',
      'settings.phone': 'Telèfon',
      'settings.email': 'Correu electrònic',

      // Settings - Agreement
      'settings.agreement': 'Conveni col·lectiu',
      'settings.ccaa': 'Comunitat Autònoma',
      'settings.tolerance': 'Tolerància de fitxatge (minuts)',
      'settings.vacation_days': 'Dies de vacances per any',

      // Settings - Calendar
      'settings.cal_year': 'Any del calendari laboral',
      'settings.weekly_hours': 'Hores setmanals ordinàries',
      'settings.work_days': 'Dies laborables per setmana',
      'settings.work_days_5': 'Dilluns a Divendres',
      'settings.work_days_6': 'Dilluns a Dissabte',
      'settings.work_days_7': 'Tots els dies',

      // Settings - Holidays
      'settings.holiday_year': 'Any',
      'settings.holidays_registered': 'Festius registrats',
      'settings.holiday_date': 'Data',
      'settings.holiday_name': 'Nom',
      'settings.holiday_type': 'Tipus',
      'settings.holiday_name_placeholder': 'Nom del festiu',
      'settings.holidays.loading': 'Carregant festius…',
      'settings.holidays.none': 'No hi ha festius registrats',
      'settings.holiday_type_national': 'Nacional',
      'settings.holiday_type_regional': 'Autonòmic',
      'settings.holiday_type_local': 'Local',

      // Settings - Notifications
      'settings.notif_email': 'Notificacions per correu',
      'settings.notif_email_all': 'Totes les notificacions',
      'settings.notif_email_important': 'Només importants',
      'settings.notif_email_none': 'Cap',
      'settings.notif_clock': 'Recordatori de fitxatge',
      'settings.notif_clock_15': '15 minuts després de l\'inici',
      'settings.notif_clock_30': '30 minuts després de l\'inici',
      'settings.notif_clock_60': '1 hora després de l\'inici',
      'settings.notif_clock_0': 'No recordar',
      'settings.notif_vacation': 'Avís de vacances pendents',
      'settings.notif_vacation_weekly': 'Setmanal',
      'settings.notif_vacation_monthly': 'Mensual',
      'settings.notif_vacation_never': 'Mai',

      // CCAA
      'ccaa.select': 'Seleccionar…',
      'ccaa.andalucia': 'Andalusia',
      'ccaa.aragon': 'Aragó',
      'ccaa.asturias': 'Astúries',
      'ccaa.baleares': 'Illes Balears',
      'ccaa.canarias': 'Canàries',
      'ccaa.cantabria': 'Cantàbria',
      'ccaa.castilla_mancha': 'Castella-La Manxa',
      'ccaa.castilla_leon': 'Castella i Lleó',
      'ccaa.catalunya': 'Catalunya',
      'ccaa.extremadura': 'Extremadura',
      'ccaa.galicia': 'Galícia',
      'ccaa.madrid': 'Comunitat de Madrid',
      'ccaa.murcia': 'Regió de Múrcia',
      'ccaa.navarra': 'Navarra',
      'ccaa.pais_vasco': 'País Basc',
      'ccaa.rioja': 'La Rioja',
      'ccaa.valencia': 'Comunitat Valenciana',

      // Toast messages
      'toast.employee_deleted': 'Empleat eliminat correctament',
      'toast.employee_delete_error': 'Error en eliminar l\'empleat',
      'toast.employee_created': 'Empleat creat',
      'toast.employee_updated': 'Empleat actualitzat',
      'toast.employee_save_error': 'Error en desar l\'empleat',
      'toast.name_required': 'El nom és obligatori',
      'toast.shift_assigned': 'Torn assignat correctament',
      'toast.shift_assign_error': 'Error en assignar torn',
      'toast.shift_deleted': 'Torn eliminat correctament',
      'toast.shift_delete_error': 'Error en eliminar el torn',
      'toast.shift_created': 'Torn creat',
      'toast.shift_updated': 'Torn actualitzat',
      'toast.shift_save_error': 'Error en desar el torn',
      'toast.fields_required': 'Completa tots els camps',
      'toast.fields_required_some': 'Completa els camps obligatoris',
      'toast.vacation_approved': 'Vacances aprovades',
      'toast.vacation_approve_error': 'Error en aprovar',
      'toast.vacation_rejected': 'Vacances rebutjades',
      'toast.vacation_reject_error': 'Error en rebutjar',
      'toast.vacation_created': 'Sol·licitud creada',
      'toast.vacation_create_error': 'Error en crear la sol·licitud',
      'toast.leave_closed': 'Baixa tancada correctament',
      'toast.leave_close_error': 'Error en tancar la baixa',
      'toast.leave_registered': 'Baixa registrada',
      'toast.leave_register_error': 'Error en registrar la baixa',
      'toast.settings_saved': 'Configuració desada correctament',
      'toast.settings_save_error': 'Error en desar la configuració',
      'toast.holiday_added': 'Festiu afegit',
      'toast.holiday_add_error': 'Error en afegir festiu',
      'toast.holiday_deleted': 'Festiu eliminat',
      'toast.holiday_delete_error': 'Error en eliminar',
      'toast.holiday_fields_required': 'Completa data i nom del festiu',
      'toast.report_downloaded': 'Informe descarregat correctament',
      'toast.report_download_error': 'Error en descarregar l\'informe',
      'toast.pin_encrypted': 'El PIN està xifrat i no es pot mostrar',
      'toast.pin_load_error': 'No s\'ha pogut carregar el PIN',
      'toast.day_detail': 'Detall del dia — próximament',
      'toast.qr_generate_first': 'Genera primer el codi QR',
      'toast.qr_downloaded': 'QR descarregat',
      'toast.qr_load_error': 'Carregant llibreria QR...',
      'toast.qr_generate_error': 'Error en generar QR',
      'toast.popup_required': 'Permet finestres emergents per imprimir',

      // NFC
      'nfc.approach': 'Apropa la targeta NFC al dispositiu...',
      'nfc.read_success': 'Targeta NFC llegida correctament',
      'nfc.read_error': 'Error en llegir la targeta. Torna-ho a provar.',
      'nfc.scan_error': 'Error en iniciar l\'escàner: ',
      'nfc.not_available': 'Web NFC no està disponible en aquest navegador. Introdueix l\'UID manualment. L\'UID sol estar imprès a la targeta o pots llegir-lo amb una app NFC.',

      // Language selector
      'lang.label': 'Idioma',

      // Misc
      'misc.documentation_arrow': 'Documentació →',
      'misc.select_placeholder': 'Seleccionar…'
    },

    en: {
      // App / meta
      'app.title': 'TalentUP Fichaje',
      'app.subtitle': 'Management panel for hospitality',
      'app.version': 'v2.0.0',

      // Login
      'login.email': 'Email',
      'login.password': 'Password',
      'login.button': 'Sign in',
      'login.demo': 'Enter demo mode',
      'login.help': 'Need help?',
      'login.docs': 'Documentation',
      'login.error_empty': 'Please fill in all fields',
      'login.loading': 'Signing in…',
      'login.error_credentials': 'Incorrect credentials. Check your email and password.',

      // Demo banner
      'demo.banner': 'Demo mode — displayed data is not real',

      // Navigation
      'nav.dashboard': 'Dashboard',
      'nav.employees': 'Employees',
      'nav.calendar': 'Calendar',
      'nav.shifts': 'Shifts',
      'nav.clocking': 'Clocking',
      'nav.vacations': 'Vacations',
      'nav.leave': 'Leave',
      'nav.reports': 'Reports',
      'nav.settings': 'Settings',

      // Buttons
      'button.login': 'Sign in',
      'button.logout': 'Sign out',
      'button.logout_short': 'Exit',
      'button.save': 'Save',
      'button.cancel': 'Cancel',
      'button.delete': 'Delete',
      'button.edit': 'Edit',
      'button.add': 'Add',
      'button.assign': 'Assign',
      'button.approve': 'Approve',
      'button.reject': 'Reject',
      'button.generate': 'Generate report',
      'button.export_pdf': 'Export PDF',
      'button.export_excel': 'Export Excel',
      'button.save_settings': 'Save settings',
      'button.add_employee': 'Add employee',
      'button.create_shift': 'Create shift',
      'button.new_request': 'New request',
      'button.register_leave': 'Register leave',
      'button.scan_nfc': 'Scan NFC',
      'button.download_qr': 'Download QR',
      'button.print_qr': 'Print QR',
      'button.give_discharge': 'Discharge',
      'button.weekly': 'Weekly',
      'button.monthly': 'Monthly',
      'button.today': 'Today',

      // Status
      'status.online': 'Online',
      'status.offline': 'Offline',
      'status.demo': 'Demo',
      'status.loading': 'Loading…',
      'status.ok': 'OK',
      'status.late': 'Late',
      'status.incident': 'Incident',
      'status.active': 'Active',
      'status.inactive': 'Inactive',
      'status.on_vacation': 'On vacation',
      'status.on_leave': 'On leave',
      'status.pending': 'Pending',
      'status.approved': 'Approved',
      'status.rejected': 'Rejected',
      'status.finished': 'Finished',
      'status.active_leave': 'Active',
      'status.not_available': 'Not available',

      // Table headers
      'table.name': 'Name',
      'table.dni': 'ID',
      'table.nss': 'SSN',
      'table.category': 'Category',
      'table.contract': 'Contract',
      'table.shift': 'Shift',
      'table.pin': 'PIN',
      'table.status': 'Status',
      'table.actions': 'Actions',
      'table.action': 'Action',
      'table.employee': 'Employee',
      'table.type': 'Type',
      'table.time': 'Time',
      'table.date': 'Date',
      'table.from': 'From',
      'table.to': 'To',
      'table.days': 'Days',
      'table.start': 'Start',
      'table.expected_end': 'Expected end',

      // Clock types
      'clock.in': 'Clock in',
      'clock.out': 'Clock out',
      'clock.break_start': 'Break',
      'clock.break_end': 'Return',
      'clock.history': 'Complete clocking history',
      'clock.today': 'Today\'s clocking',

      // Modal
      'modal.confirm_delete': 'Delete this item?',
      'modal.confirm_delete_employee': 'Delete this employee?',
      'modal.confirm_delete_shift': 'Delete this shift?',
      'modal.confirm_delete_holiday': 'Delete this holiday?',
      'modal.confirm_close_leave': 'Confirm medical discharge?',
      'modal.confirm_save': 'Save changes?',
      'modal.cancel': 'Cancel',
      'modal.save': 'Save',
      'modal.assign_shift': 'Assign shift',
      'modal.select_shift': 'Select shift',
      'modal.no_shift': 'No shift (rest)',
      'modal.reject_request': 'Reject request',
      'modal.reject_reason': 'Rejection reason',
      'modal.reject_reason_placeholder': 'State the reason…',
      'modal.reject_reason_required': 'Provide a reason for rejection',

      // Employee modal
      'modal.edit_employee': 'Edit employee',
      'modal.add_employee': 'Add employee',
      'modal.first_name': 'First name',
      'modal.last_name': 'Last name',
      'modal.dni_nie': 'ID / NIE',
      'modal.ssn': 'Social Security Number',
      'modal.professional_category': 'Professional category',
      'modal.contract_type': 'Contract type',
      'modal.default_shift': 'Default shift',
      'modal.no_shift_option': 'No shift',
      'modal.employee_status': 'Status',
      'modal.pin_label': 'PIN (4 digits) — only if changed',
      'modal.pin_placeholder': 'Leave empty to keep current',
      'modal.nfc_card': 'NFC card (UID)',
      'modal.employee_qr': 'Employee QR code',
      'modal.select_placeholder': 'Select…',

      // Contract types
      'contract.IND': 'Permanent',
      'contract.TEM-OC': 'Temporary (project)',
      'contract.TEM-CIR': 'Temporary (circumstances)',
      'contract.TEM-INT': 'Interim',
      'contract.PAR-IND': 'Part-time permanent',
      'contract.PAR-TEMP': 'Part-time temporary',

      // Shift modal
      'modal.edit_shift': 'Edit shift',
      'modal.create_shift': 'Create shift',
      'modal.shift_name': 'Shift name',
      'modal.shift_start': 'Start time',
      'modal.shift_end': 'End time',
      'modal.shift_type': 'Shift type',
      'modal.tolerance': 'Tolerance (minutes)',
      'modal.shift_color': 'Shift color',

      // Shift types
      'shift_type.morning': 'Morning',
      'shift_type.afternoon': 'Afternoon',
      'shift_type.night': 'Night',
      'shift_type.split': 'Split',
      'shift_type.rotating': 'Rotating',
      'shift_type.custom': 'Custom',

      // Vacation modal
      'modal.new_vacation': 'New vacation request',
      'modal.start_date': 'Start date',
      'modal.end_date': 'End date',
      'modal.vacation_type': 'Type',
      'modal.vacation_reason': 'Reason (optional)',
      'modal.vacation_reason_placeholder': 'Reason for request…',

      // Vacation types
      'vacation.vacation': 'Vacation',
      'vacation.personal_leave': 'Personal leave',
      'vacation.unpaid_leave': 'Unpaid leave',

      // Leave modal
      'modal.register_leave': 'Register medical leave',
      'modal.leave_type': 'Leave type',
      'modal.expected_end': 'Expected end',
      'modal.diagnosis': 'Diagnosis (optional)',
      'modal.diagnosis_placeholder': 'Code / description',

      // Leave types
      'leave.EC': 'Common Illness',
      'leave.EC_short': 'Common Ill.',
      'leave.ANL': 'Non-Work Accident',
      'leave.ANL_short': 'Non-Work Acc.',
      'leave.AL': 'Work Accident',
      'leave.AL_short': 'Work Acc.',
      'leave.EP': 'Occupational Disease',
      'leave.EP_short': 'Occ. Disease',
      'leave.MAT': 'Maternity',
      'leave.PAT': 'Paternity',

      // Pages - Dashboard
      'page.dashboard.title': 'Dashboard',
      'page.dashboard.subtitle': 'Executive activity summary',
      'dashboard.active_today': 'Active employees today',
      'dashboard.clocks_today': 'Clocking today',
      'dashboard.incidents': 'Pending incidents',
      'dashboard.overtime_week': 'Overtime this week',
      'dashboard.no_clock': 'Not clocked in today',
      'dashboard.pending_vacations': 'Pending vacations',
      'dashboard.all_clocked': 'Everyone has clocked in',
      'dashboard.no_pending': 'No pending requests',
      'dashboard.no_clocks_today': 'No clocking today',
      'dashboard.no_data': 'No data available — server not responding',
      'dashboard.more': 'more',

      // Pages - Empleados
      'page.employees.title': 'Employees',
      'page.employees.subtitle': 'Full workforce management',
      'employees.search_placeholder': 'Search name, ID, SSN…',
      'employees.filter_all_status': 'All statuses',
      'employees.filter_active': 'Active',
      'employees.filter_inactive': 'Inactive',
      'employees.filter_on_vacation': 'On vacation',
      'employees.filter_on_leave': 'On leave',
      'employees.filter_all_shifts': 'All shifts',
      'employees.no_results': 'No employees match the filters',
      'employees.load_error': 'Could not load employees — server not responding',

      // Pages - Calendario
      'page.calendar.title': 'Calendar',
      'page.calendar.subtitle': 'Monthly view with shifts, holidays and vacations',
      'calendar.loading': 'Loading calendar…',
      'calendar.load_employees_first': 'Load employees first',
      'calendar.holiday': 'Holiday',
      'calendar.shift': 'Shift',

      // Pages - Turnos
      'page.shifts.title': 'Shifts',
      'page.shifts.subtitle': 'Work shift configuration',
      'shifts.loading': 'Loading shifts…',
      'shifts.none': 'No shifts configured',
      'shifts.load_error': 'Could not load shifts — server not responding',
      'shifts.tolerance': 'Tolerance',

      // Pages - Fichajes
      'page.clocking.title': 'Clocking',
      'page.clocking.subtitle': 'Complete clocking history',
      'clocking.filter_all_employees': 'All employees',
      'clocking.filter_all_types': 'All types',
      'clocking.filter_all_status': 'All statuses',
      'clocking.no_results': 'No clocking matches the filters',
      'clocking.load_error': 'Could not load clocking — server not responding',

      // Pages - Vacaciones
      'page.vacations.title': 'Vacations and Leave',
      'page.vacations.subtitle': 'Request and calendar management',
      'vacations.pending': 'Pending requests',
      'vacations.calendar': 'Vacation calendar',
      'vacations.none': 'No vacation requests',
      'vacations.no_approved': 'No approved vacations',
      'vacations.loading': 'Loading requests…',
      'vacations.load_error': 'Could not load requests — server not responding',

      // Pages - Bajas
      'page.leave.title': 'Leave (IT)',
      'page.leave.subtitle': 'Temporary disability and leave records',
      'leave.filter_all': 'All leaves',
      'leave.filter_active': 'Active',
      'leave.filter_finished': 'Finished',
      'leave.filter_all_types': 'All types',
      'leave.no_results': 'No leaves match the filters',
      'leave.loading': 'Loading leaves…',
      'leave.load_error': 'Could not load leaves — server not responding',

      // Pages - Informes
      'page.reports.title': 'Reports',
      'page.reports.subtitle': 'Hours, absenteeism and labor cost reports',
      'reports.from': 'From',
      'reports.to': 'To',
      'reports.type': 'Report type',
      'reports.type_hours': 'Worked hours',
      'reports.type_overtime': 'Overtime',
      'reports.type_absenteeism': 'Absenteeism',
      'reports.type_labor_costs': 'Labor costs',
      'reports.type_inspection': 'Labor inspection',
      'reports.type_payroll': 'Payroll',
      'reports.title_hours': 'Hours per employee',
      'reports.empty': 'Select a date range and generate the report',
      'reports.no_data': 'No data in the selected period',
      'reports.col_regular_hours': 'Regular hours',
      'reports.col_overtime_hours': 'Overtime',
      'reports.col_total': 'Total',
      'reports.col_absent_days': 'Absent days',
      'reports.col_rate': 'Rate',
      'reports.col_base_salary': 'Base salary',
      'reports.col_complements': 'Complements',
      'reports.col_overtime_amount': 'Overtime',
      'reports.col_scheduled': 'Scheduled',
      'reports.col_worked': 'Worked',
      'reports.col_holidays': 'Holidays',
      'reports.col_absences': 'Absences',
      'reports.col_clock_in': 'Clock in',
      'reports.col_clock_out': 'Clock out',
      'reports.col_minutes': 'Minutes',
      'reports.overtime_structural': 'Structural',
      'reports.overtime_force_majeure': 'Force Majeure',
      'reports.compensation_pending': 'Pending',

      // Settings
      'page.settings.title': 'Settings',
      'page.settings.subtitle': 'Restaurant data, agreement and preferences',
      'settings.tab_restaurant': 'Restaurant',
      'settings.tab_agreement': 'Agreement',
      'settings.tab_calendar': 'Work calendar',
      'settings.tab_holidays': 'Holidays',
      'settings.tab_notifications': 'Notifications',
      'settings.language': 'Language',
      'settings.theme': 'Theme',
      'settings.notifications': 'Notifications',

      // Settings - Restaurant
      'settings.restaurant_name': 'Restaurant name',
      'settings.cif': 'Tax ID',
      'settings.address': 'Address',
      'settings.phone': 'Phone',
      'settings.email': 'Email',

      // Settings - Agreement
      'settings.agreement': 'Collective agreement',
      'settings.ccaa': 'Autonomous Community',
      'settings.tolerance': 'Clocking tolerance (minutes)',
      'settings.vacation_days': 'Vacation days per year',

      // Settings - Calendar
      'settings.cal_year': 'Work calendar year',
      'settings.weekly_hours': 'Weekly regular hours',
      'settings.work_days': 'Workdays per week',
      'settings.work_days_5': 'Monday to Friday',
      'settings.work_days_6': 'Monday to Saturday',
      'settings.work_days_7': 'Every day',

      // Settings - Holidays
      'settings.holiday_year': 'Year',
      'settings.holidays_registered': 'Registered holidays',
      'settings.holiday_date': 'Date',
      'settings.holiday_name': 'Name',
      'settings.holiday_type': 'Type',
      'settings.holiday_name_placeholder': 'Holiday name',
      'settings.holidays.loading': 'Loading holidays…',
      'settings.holidays.none': 'No holidays registered',
      'settings.holiday_type_national': 'National',
      'settings.holiday_type_regional': 'Regional',
      'settings.holiday_type_local': 'Local',

      // Settings - Notifications
      'settings.notif_email': 'Email notifications',
      'settings.notif_email_all': 'All notifications',
      'settings.notif_email_important': 'Important only',
      'settings.notif_email_none': 'None',
      'settings.notif_clock': 'Clocking reminder',
      'settings.notif_clock_15': '15 minutes after start',
      'settings.notif_clock_30': '30 minutes after start',
      'settings.notif_clock_60': '1 hour after start',
      'settings.notif_clock_0': 'No reminder',
      'settings.notif_vacation': 'Pending vacation notice',
      'settings.notif_vacation_weekly': 'Weekly',
      'settings.notif_vacation_monthly': 'Monthly',
      'settings.notif_vacation_never': 'Never',

      // CCAA
      'ccaa.select': 'Select…',
      'ccaa.andalucia': 'Andalusia',
      'ccaa.aragon': 'Aragon',
      'ccaa.asturias': 'Asturias',
      'ccaa.baleares': 'Balearic Islands',
      'ccaa.canarias': 'Canary Islands',
      'ccaa.cantabria': 'Cantabria',
      'ccaa.castilla_mancha': 'Castile-La Mancha',
      'ccaa.castilla_leon': 'Castile and Leon',
      'ccaa.catalunya': 'Catalonia',
      'ccaa.extremadura': 'Extremadura',
      'ccaa.galicia': 'Galicia',
      'ccaa.madrid': 'Community of Madrid',
      'ccaa.murcia': 'Region of Murcia',
      'ccaa.navarra': 'Navarre',
      'ccaa.pais_vasco': 'Basque Country',
      'ccaa.rioja': 'La Rioja',
      'ccaa.valencia': 'Valencian Community',

      // Toast messages
      'toast.employee_deleted': 'Employee deleted successfully',
      'toast.employee_delete_error': 'Error deleting employee',
      'toast.employee_created': 'Employee created',
      'toast.employee_updated': 'Employee updated',
      'toast.employee_save_error': 'Error saving employee',
      'toast.name_required': 'Name is required',
      'toast.shift_assigned': 'Shift assigned successfully',
      'toast.shift_assign_error': 'Error assigning shift',
      'toast.shift_deleted': 'Shift deleted successfully',
      'toast.shift_delete_error': 'Error deleting shift',
      'toast.shift_created': 'Shift created',
      'toast.shift_updated': 'Shift updated',
      'toast.shift_save_error': 'Error saving shift',
      'toast.fields_required': 'Please fill in all fields',
      'toast.fields_required_some': 'Please fill in required fields',
      'toast.vacation_approved': 'Vacation approved',
      'toast.vacation_approve_error': 'Error approving',
      'toast.vacation_rejected': 'Vacation rejected',
      'toast.vacation_reject_error': 'Error rejecting',
      'toast.vacation_created': 'Request created',
      'toast.vacation_create_error': 'Error creating request',
      'toast.leave_closed': 'Leave closed successfully',
      'toast.leave_close_error': 'Error closing leave',
      'toast.leave_registered': 'Leave registered',
      'toast.leave_register_error': 'Error registering leave',
      'toast.settings_saved': 'Settings saved successfully',
      'toast.settings_save_error': 'Error saving settings',
      'toast.holiday_added': 'Holiday added',
      'toast.holiday_add_error': 'Error adding holiday',
      'toast.holiday_deleted': 'Holiday deleted',
      'toast.holiday_delete_error': 'Error deleting',
      'toast.holiday_fields_required': 'Fill in date and holiday name',
      'toast.report_downloaded': 'Report downloaded successfully',
      'toast.report_download_error': 'Error downloading report',
      'toast.pin_encrypted': 'PIN is encrypted and cannot be displayed',
      'toast.pin_load_error': 'Could not load PIN',
      'toast.day_detail': 'Day detail — coming soon',
      'toast.qr_generate_first': 'Generate the QR code first',
      'toast.qr_downloaded': 'QR downloaded',
      'toast.qr_load_error': 'Loading QR library...',
      'toast.qr_generate_error': 'Error generating QR',
      'toast.popup_required': 'Allow pop-ups to print',

      // NFC
      'nfc.approach': 'Bring the NFC card close to the device...',
      'nfc.read_success': 'NFC card read successfully',
      'nfc.read_error': 'Error reading the card. Try again.',
      'nfc.scan_error': 'Error starting scanner: ',
      'nfc.not_available': 'Web NFC is not available in this browser. Enter the UID manually. The UID is usually printed on the card or you can read it with an NFC app.',

      // Language selector
      'lang.label': 'Language',

      // Misc
      'misc.documentation_arrow': 'Documentation →',
      'misc.select_placeholder': 'Select…'
    }
  };

  // ===== STATE =====
  const STORAGE_KEY = 'talentup_lang';
  const SUPPORTED = ['es', 'ca', 'en'];
  const DEFAULT_LANG = 'es';
  let currentLang = DEFAULT_LANG;

  // ===== API =====

  /**
   * Get the current language code.
   * @returns {string} 'es' | 'ca' | 'en'
   */
  function getCurrentLanguage() {
    return currentLang;
  }

  /**
   * Get list of supported languages.
   * @returns {string[]}
   */
  function getSupportedLanguages() {
    return SUPPORTED.slice();
  }

  /**
   * Translate a key to the current language.
   * Supports dotted keys (e.g. 'nav.dashboard').
   * Falls back to ES, then to the key itself.
   * @param {string} key
   * @returns {string}
   */
  function t(key) {
    var dict = translations[currentLang] || translations[DEFAULT_LANG];
    if (dict && Object.prototype.hasOwnProperty.call(dict, key)) {
      return dict[key];
    }
    // Fallback to default language
    var fallback = translations[DEFAULT_LANG];
    if (fallback && Object.prototype.hasOwnProperty.call(fallback, key)) {
      return fallback[key];
    }
    // Last resort: return the key
    return key;
  }

  /**
   * Set the current language, persist to localStorage, update DOM.
   * @param {string} lang — 'es' | 'ca' | 'en'
   */
  function setLanguage(lang) {
    if (SUPPORTED.indexOf(lang) === -1) {
      lang = DEFAULT_LANG;
    }
    currentLang = lang;
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch (e) {
      // localStorage might be unavailable (private mode etc.)
    }
    // Update <html lang="...">
    document.documentElement.setAttribute('lang', lang);
    // Apply translations to DOM
    applyTranslations();
    // Update active state of language selector
    updateLangSelector();
    // Dispatch event so app code can re-render dynamic content
    document.dispatchEvent(new CustomEvent('languagechange', { detail: { lang: lang } }));
  }

  /**
   * Apply translations to all elements with data-i18n attributes.
   * - data-i18n="key" → sets textContent
   * - data-i18n-placeholder="key" → sets placeholder
   * - data-i18n-title="key" → sets title attribute
   */
  function applyTranslations() {
    // Text content
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var key = el.getAttribute('data-i18n');
      el.textContent = t(key);
    });
    // Placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
      var key = el.getAttribute('data-i18n-placeholder');
      el.setAttribute('placeholder', t(key));
    });
    // Title attributes
    document.querySelectorAll('[data-i18n-title]').forEach(function (el) {
      var key = el.getAttribute('data-i18n-title');
      el.setAttribute('title', t(key));
    });
    // Options: data-i18n on <option> sets text
    // (handled by the generic textContent loop above)
  }

  /**
   * Update the visual active state of language selector buttons.
   */
  function updateLangSelector() {
    document.querySelectorAll('.lang-btn').forEach(function (btn) {
      var lang = btn.getAttribute('data-lang');
      if (lang === currentLang) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  /**
   * Initialize the i18n system.
   * Reads stored preference, falls back to browser language, then to ES.
   */
  function init() {
    var stored = null;
    try {
      stored = localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      // ignore
    }
    if (stored && SUPPORTED.indexOf(stored) !== -1) {
      currentLang = stored;
    } else {
      // Try browser language
      var browserLang = (navigator.language || 'es').toLowerCase().slice(0, 2);
      if (SUPPORTED.indexOf(browserLang) !== -1) {
        currentLang = browserLang;
      } else {
        currentLang = DEFAULT_LANG;
      }
    }
    document.documentElement.setAttribute('lang', currentLang);
    applyTranslations();
    updateLangSelector();
  }

  // Auto-init on DOMContentLoaded (or immediately if already loaded)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Export to global scope
  global.i18n = {
    t: t,
    setLanguage: setLanguage,
    getCurrentLanguage: getCurrentLanguage,
    getSupportedLanguages: getSupportedLanguages,
    applyTranslations: applyTranslations,
    init: init
  };

  // Also export `t` directly for convenience in inline JS
  global.t = t;

})(typeof window !== 'undefined' ? window : this);