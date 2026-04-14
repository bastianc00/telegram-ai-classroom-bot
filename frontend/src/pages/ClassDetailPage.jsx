import { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  ArrowLeft,
  Play,
  FileText,
  Calendar,
  Clock,
  Trash2,
  Edit,
  Download,
  History,
  Loader2
} from 'lucide-react';
import { classesAPI, instancesAPI } from '@/services/api';

export const ClassDetailPage = () => {
  const { classId } = useParams();
  const navigate = useNavigate();
  const [classData, setClassData] = useState(null);
  const [instances, setInstances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadClassData();
  }, [classId]);

  const loadClassData = async () => {
    try {
      setLoading(true);

      // Load class data
      const classResponse = await classesAPI.getById(classId);
      setClassData(classResponse.class);

      // Load instances
      const instancesResponse = await instancesAPI.getAll(classId);
      setInstances(instancesResponse.instances || []);

      setLoading(false);
    } catch (err) {
      console.error('Error loading class data:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const handleStartClass = () => {
    navigate(`/classes/${classId}/start`);
  };

  const handleDelete = async () => {
    if (confirm('¿Estás seguro de que quieres eliminar esta clase?')) {
      try {
        await classesAPI.delete(classId);
        navigate('/home');
      } catch (err) {
        console.error('Error deleting class:', err);
        alert('Error al eliminar la clase');
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Cargando información de la clase...</p>
        </div>
      </div>
    );
  }

  if (error || !classData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Clase no encontrada'}</p>
          <Button onClick={() => navigate('/home')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Volver al Inicio
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild>
              <Link to="/home">
                <ArrowLeft className="h-5 w-5" />
              </Link>
            </Button>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">{classData.title}</h1>
              <p className="text-sm text-gray-500">{classData.subject}</p>
            </div>
            <Button onClick={handleStartClass} size="lg">
              <Play className="mr-2 h-5 w-5" />
              Iniciar Clase
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Main Info */}
          <div className="lg:col-span-2 space-y-6">
            {/* Overview Card */}
            <Card>
              <CardHeader>
                <CardTitle>Información General</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {classData.description && (
                  <>
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-1">Descripción</h3>
                      <p className="text-gray-900">{classData.description}</p>
                    </div>
                    <Separator />
                  </>
                )}

                <div className="grid grid-cols-2 gap-4">
                  {classData.subject && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-1">Asignatura</h3>
                      <Badge variant="secondary">{classData.subject}</Badge>
                    </div>
                  )}
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-1">Diapositivas</h3>
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-gray-400" />
                      <span className="font-medium">{classData.slides_count || 0} slides</span>
                    </div>
                  </div>
                </div>

                <Separator />

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-1">Creada</h3>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-gray-400" />
                      <span>{new Date(classData.created_at).toLocaleDateString('es-ES')}</span>
                    </div>
                  </div>
                  {classData.updated_at && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-1">Actualizada</h3>
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-gray-400" />
                        <span>{new Date(classData.updated_at).toLocaleDateString('es-ES')}</span>
                      </div>
                    </div>
                  )}
                </div>

                {classData.file_name && (
                  <>
                    <Separator />
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-1">Archivo</h3>
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-gray-400" />
                        <span className="font-medium">{classData.file_name}</span>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Instances History */}
            <Card>
              <CardHeader>
                <CardTitle>Historial de Instancias</CardTitle>
                <CardDescription>
                  Registro de todas las veces que se ha dictado esta clase
                </CardDescription>
              </CardHeader>
              <CardContent>
                {instances.length === 0 ? (
                  <div className="text-center py-8">
                    <History className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">No hay instancias registradas aún</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {instances.map((instance) => {
                      const startTime = new Date(instance.start_time);
                      const isActive = !instance.end_time;
                      const duration = instance.duration_minutes || 0;

                      return (
                        <div
                          key={instance.id}
                          className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                        >
                          <div className="flex items-center gap-4">
                            <div className={`p-3 rounded-lg ${isActive ? 'bg-green-100' : 'bg-blue-100'}`}>
                              <Calendar className={`h-5 w-5 ${isActive ? 'text-green-600' : 'text-blue-600'}`} />
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">
                                {startTime.toLocaleDateString('es-ES', {
                                  weekday: 'long',
                                  year: 'numeric',
                                  month: 'long',
                                  day: 'numeric'
                                })}
                              </p>
                              <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                                {!isActive && duration > 0 && (
                                  <span className="flex items-center gap-1">
                                    <Clock className="h-3 w-3" />
                                    {duration} min
                                  </span>
                                )}
                                {isActive && (
                                  <Badge variant="default" className="bg-green-600">
                                    En curso
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>
                          {!isActive && (
                            <Button variant="outline" size="sm" asChild>
                              <Link to={`/classes/${classId}/instances/${instance.id}`}>
                                Ver Reporte
                              </Link>
                            </Button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Actions & Stats */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Acciones</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button className="w-full justify-start" onClick={handleStartClass}>
                  <Play className="mr-2 h-4 w-4" />
                  Iniciar Nueva Instancia
                </Button>
                <Button variant="outline" className="w-full justify-start" asChild>
                  <Link to={`/classes/${classId}/edit`}>
                    <Edit className="mr-2 h-4 w-4" />
                    Editar Información
                  </Link>
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <Download className="mr-2 h-4 w-4" />
                  Descargar Presentación
                </Button>
                <Separator />
                <Button
                  variant="destructive"
                  className="w-full justify-start"
                  onClick={handleDelete}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Eliminar Clase
                </Button>
              </CardContent>
            </Card>

            {/* Stats */}
            <Card>
              <CardHeader>
                <CardTitle>Estadísticas</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-gray-500">Instancias realizadas</span>
                    <span className="text-2xl font-bold">{instances.length}</span>
                  </div>
                </div>
                {instances.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-500">Duración promedio</span>
                        <span className="text-2xl font-bold">
                          {(() => {
                            const completedInstances = instances.filter(inst => inst.end_time && inst.duration_minutes);
                            if (completedInstances.length === 0) return '-';

                            const avgDuration = completedInstances.reduce((sum, inst) => {
                              return sum + inst.duration_minutes;
                            }, 0) / completedInstances.length;

                            return Math.round(avgDuration);
                          })()} min
                        </span>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
};
