import { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  ArrowLeft,
  Calendar,
  Clock,
  FileText,
  TrendingUp,
  Sparkles,
  CheckCircle,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { instancesAPI, classesAPI } from '@/services/api';
import { Alert, AlertDescription } from '@/components/ui/alert';

export const InstanceReportPage = () => {
  const { classId, instanceId } = useParams();
  const navigate = useNavigate();

  const [instance, setInstance] = useState(null);
  const [classData, setClassData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch instance data with AI content
        const instanceResponse = await instancesAPI.getById(classId, instanceId);
        setInstance(instanceResponse.instance);

        // Fetch class data to get class name and total slides
        const classResponse = await classesAPI.getById(classId);
        setClassData(classResponse.class);

      } catch (err) {
        console.error('Error fetching instance data:', err);
        setError(err.message || 'Error al cargar los datos de la instancia');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [classId, instanceId]);

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;

    if (mins > 0) {
      return `${mins} min ${secs} seg`;
    }
    return `${secs} seg`;
  };

  const formatTime = (isoString) => {
    if (!isoString) return '--:--';
    const date = new Date(isoString);
    return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (isoString) => {
    if (!isoString) return '--';
    const date = new Date(isoString);
    return date.toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });
  };

  // Get unique slides viewed
  const getUniqueSlides = (slideFlow) => {
    if (!slideFlow || slideFlow.length === 0) return 0;
    return new Set(slideFlow).size;
  };

  // Análisis de Mapa de Atención
  const getAttentionMapData = () => {
    if (!instance || !instance.slide_times || Object.keys(instance.slide_times).length === 0) {
      return null;
    }

    const times = Object.values(instance.slide_times);
    const avgTime = times.reduce((sum, t) => sum + t, 0) / times.length;

    const slideData = Object.entries(instance.slide_times)
      .map(([slideNum, time]) => {
        const percentage = (time / avgTime) * 100;
        let difficulty = 'normal';
        if (percentage > 150) {
          difficulty = 'problematic'; // Rojo - >150% del promedio
        } else if (percentage < 50) {
          difficulty = 'fast'; // Verde - <50% del promedio
        }

        return {
          slideNum: parseInt(slideNum),
          time,
          percentage,
          difficulty
        };
      })
      .sort((a, b) => a.slideNum - b.slideNum);

    const problematicSlides = slideData.filter(s => s.difficulty === 'problematic');
    const fastSlides = slideData.filter(s => s.difficulty === 'fast');

    return {
      avgTime,
      slideData,
      problematicSlides,
      fastSlides
    };
  };

  const attentionMap = getAttentionMapData();

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Cargando reporte...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" asChild>
                <Link to={`/classes/${classId}`}>
                  <ArrowLeft className="h-5 w-5" />
                </Link>
              </Button>
              <h1 className="text-2xl font-bold text-gray-900">Reporte de Instancia</h1>
            </div>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <Button
            onClick={() => navigate(`/classes/${classId}`)}
            className="mt-4"
          >
            Volver a la clase
          </Button>
        </main>
      </div>
    );
  }

  // No data state
  if (!instance || !classData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No se encontraron datos de la instancia</p>
          <Button
            onClick={() => navigate(`/classes/${classId}`)}
            className="mt-4"
          >
            Volver a la clase
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
              <Link to={`/classes/${classId}`}>
                <ArrowLeft className="h-5 w-5" />
              </Link>
            </Button>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">Reporte de Instancia</h1>
              <p className="text-sm text-gray-500">{classData.title}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-blue-100 rounded-lg">
                    <Calendar className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Fecha</p>
                    <p className="text-lg font-bold">
                      {formatDate(instance.start_time)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-green-100 rounded-lg">
                    <Clock className="h-6 w-6 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Duración</p>
                    <p className="text-lg font-bold">
                      {instance.end_time && instance.duration_minutes
                        ? `${instance.duration_minutes} min`
                        : 'En curso...'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-purple-100 rounded-lg">
                    <FileText className="h-6 w-6 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Diapositivas</p>
                    <p className="text-lg font-bold">
                      {getUniqueSlides(instance.slide_flow)}/{classData.slides_count || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-orange-100 rounded-lg">
                    <Sparkles className="h-6 w-6 text-orange-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Contenido IA</p>
                    <p className="text-lg font-bold">
                      {instance.ai_generated?.length || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Session Info */}
          <Card>
            <CardHeader>
              <CardTitle>Información de la Sesión</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Hora de inicio</p>
                  <p className="font-medium">{formatTime(instance.start_time)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">Hora de término</p>
                  <p className="font-medium">
                    {instance.end_time ? formatTime(instance.end_time) : 'En curso...'}
                  </p>
                </div>
              </div>
              {instance.sync_code && (
                <div>
                  <p className="text-sm text-gray-500 mb-1">Código de sincronización</p>
                  <p className="font-mono font-bold text-lg text-blue-600">{instance.sync_code}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Slide Flow */}
          {instance.slide_flow && instance.slide_flow.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Flujo de Diapositivas
                </CardTitle>
                <CardDescription>
                  Secuencia de navegación durante la clase ({instance.slide_flow.length} transiciones)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {instance.slide_flow.map((slide, index) => (
                    <div key={index} className="flex items-center">
                      <Badge variant={index === 0 ? 'default' : 'secondary'}>
                        {slide}
                      </Badge>
                      {index < instance.slide_flow.length - 1 && (
                        <span className="mx-2 text-gray-400">→</span>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Slide Times */}
          {instance.slide_times && Object.keys(instance.slide_times).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Tiempo en cada Diapositiva
                </CardTitle>
                <CardDescription>
                  Tiempo total dedicado a cada diapositiva
                  {(() => {
                    const totalTracked = Object.values(instance.slide_times).reduce((sum, time) => sum + time, 0);
                    const totalDuration = instance.duration_minutes ? instance.duration_minutes * 60 : 0;
                    if (totalDuration > 0 && totalTracked < totalDuration) {
                      const missing = totalDuration - totalTracked;
                      return ` • Total: ${formatDuration(totalTracked)}`;
                    }
                    return ` • Total: ${formatDuration(totalTracked)}`;
                  })()}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(instance.slide_times)
                    .sort(([a], [b]) => parseInt(a) - parseInt(b))
                    .map(([slideNum, time]) => {
                      const maxTime = Math.max(...Object.values(instance.slide_times));
                      return (
                        <div key={slideNum} className="flex items-center gap-3">
                          <span className="text-sm font-medium text-gray-500 w-20">
                            Slide {slideNum}
                          </span>
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-500 h-2 rounded-full transition-all"
                              style={{ width: `${(time / maxTime) * 100}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium w-16 text-right">
                            {formatDuration(time)}
                          </span>
                        </div>
                      );
                    })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Mapa de Atención */}
          {attentionMap && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Mapa de Atención - Análisis de Ritmo
                </CardTitle>
                <CardDescription>
                  Análisis del tiempo dedicado a cada diapositiva durante la clase
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Estadísticas generales */}
                <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">{formatDuration(Math.round(attentionMap.avgTime))}</p>
                    <p className="text-sm text-gray-600">Tiempo promedio</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-red-600">{attentionMap.problematicSlides.length}</p>
                    <p className="text-sm text-gray-600">Slides problemáticas</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">{attentionMap.fastSlides.length}</p>
                    <p className="text-sm text-gray-600">Slides rápidas</p>
                  </div>
                </div>

                {/* Heat Map visual */}
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-4">Mapa de Calor por Diapositiva:</p>
                  <div className="space-y-2">
                    {attentionMap.slideData.map((slide) => {
                      const maxTime = Math.max(...attentionMap.slideData.map(s => s.time));
                      const widthPercentage = (slide.time / maxTime) * 100;

                      let bgColor = 'bg-yellow-400'; // Normal
                      let textColor = 'text-yellow-700';
                      if (slide.difficulty === 'problematic') {
                        bgColor = 'bg-red-500';
                        textColor = 'text-red-700';
                      } else if (slide.difficulty === 'fast') {
                        bgColor = 'bg-green-500';
                        textColor = 'text-green-700';
                      }

                      return (
                        <div key={slide.slideNum} className="flex items-center gap-3">
                          <span className="text-sm font-medium w-20 text-gray-600">
                            Slide {slide.slideNum}
                          </span>
                          <div className="flex-1 bg-gray-200 rounded-full h-8 overflow-hidden">
                            <div
                              className={`${bgColor} h-full transition-all`}
                              style={{ width: `${widthPercentage}%` }}
                            >
                            </div>
                          </div>
                          <span className={`text-xs font-medium w-16 ${textColor}`}>
                            {slide.percentage.toFixed(0)}%
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Leyenda */}
                <div className="flex items-center justify-center gap-6 pt-4 border-t">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-red-500 rounded"></div>
                    <span className="text-sm text-gray-600">Problemática ({'>'}150%)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-yellow-400 rounded"></div>
                    <span className="text-sm text-gray-600">Normal (50-150%)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-green-500 rounded"></div>
                    <span className="text-sm text-gray-600">Rápida ({'<'}50%)</span>
                  </div>
                </div>

                {/* Insights */}
                {(attentionMap.problematicSlides.length > 0 || attentionMap.fastSlides.length > 0) && (
                  <div className="space-y-3 pt-4 border-t">
                    <p className="text-sm font-medium text-gray-700">📊 Análisis:</p>
                    {attentionMap.problematicSlides.length > 0 && (
                      <Alert className="border-red-200 bg-red-50">
                        <AlertDescription className="text-sm">
                          <strong>Slides problemáticas:</strong> {attentionMap.problematicSlides.map(s => `#${s.slideNum}`).join(', ')}
                          <br />
                          Estas diapositivas tomaron más del 150% del tiempo promedio, sugiriendo mayor dificultad o necesidad de profundización.
                        </AlertDescription>
                      </Alert>
                    )}
                    {attentionMap.fastSlides.length > 0 && (
                      <Alert className="border-green-200 bg-green-50">
                        <AlertDescription className="text-sm">
                          <strong>Slides rápidas:</strong> {attentionMap.fastSlides.map(s => `#${s.slideNum}`).join(', ')}
                          <br />
                          Estas diapositivas tomaron menos del 50% del tiempo promedio. Considera si necesitan más profundidad.
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* AI Generated Content */}
          {instance.ai_generated && instance.ai_generated.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5" />
                  Contenido Generado con IA
                </CardTitle>
                <CardDescription>
                  Ejemplos y preguntas generados durante la clase ({instance.ai_generated.length} items)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {instance.ai_generated.map((item) => (
                  <div key={item.id} className="border rounded-lg p-4 space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <Badge variant={item.content_type === 'example' ? 'default' : 'secondary'}>
                          {item.content_type === 'example' ? 'Ejemplo' : 'Pregunta'}
                        </Badge>
                        <span className="text-sm text-gray-500">
                          Slide {item.slide_number}
                          {item.created_at && ` • ${formatTime(item.created_at)}`}
                        </span>
                      </div>
                    </div>

                    {item.prompt && (
                      <>
                        <div>
                          <p className="text-sm font-medium text-gray-700 mb-2">Prompt:</p>
                          <p className="text-sm text-gray-600 italic">"{item.prompt}"</p>
                        </div>
                        <Separator />
                      </>
                    )}

                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-3">
                        {item.options && item.options.length > 0 ? 'Opciones generadas:' : 'Contenido:'}
                      </p>
                      {item.options && item.options.length > 0 ? (
                        <div className="space-y-2">
                          {item.options.map((option, index) => (
                            <div
                              key={index}
                              className={`p-3 rounded-lg border ${
                                index === item.selected_option
                                  ? 'bg-green-50 border-green-300'
                                  : 'bg-gray-50 border-gray-200'
                              }`}
                            >
                              <div className="flex items-start gap-2">
                                {index === item.selected_option && (
                                  <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                                )}
                                <div className="flex-1">
                                  <p className="text-sm font-medium text-gray-900">
                                    Opción {index + 1}
                                    {index === item.selected_option && (
                                      <span className="ml-2 text-green-600">(Seleccionada)</span>
                                    )}
                                  </p>
                                  <p className="text-sm text-gray-600 mt-1">{option}</p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="p-3 rounded-lg bg-gray-50 border border-gray-200">
                          <p className="text-sm text-gray-600">{item.content || 'Sin contenido'}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5" />
                  Contenido Generado con IA
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-500 text-center py-8">
                  No se generó contenido con IA durante esta clase
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
};
