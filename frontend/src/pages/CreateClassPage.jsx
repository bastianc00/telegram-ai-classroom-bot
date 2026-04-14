import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ArrowLeft,
  Upload,
  FileText,
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react';
import { classesAPI } from '@/services/api';

export const CreateClassPage = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // null, 'uploading', 'success', 'error'
  const [formData, setFormData] = useState({
    title: '',
    subject: '',
    level: '',
    description: '',
    file: null
  });
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validar tipo de archivo - solo PPTX
      const validTypes = [
        'application/vnd.openxmlformats-officedocument.presentationml.presentation', // .pptx
      ];

      // También validar por extensión
      const fileName = file.name.toLowerCase();
      const validExtensions = ['.pptx'];
      const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext));

      if (!validTypes.includes(file.type) && !hasValidExtension) {
        setError('Por favor selecciona un archivo PPTX válido');
        setFormData(prev => ({ ...prev, file: null }));
        return;
      }

      // Validar tamaño (max 50MB)
      if (file.size > 50 * 1024 * 1024) {
        setError('El archivo es demasiado grande. Tamaño máximo: 50MB');
        setFormData(prev => ({ ...prev, file: null }));
        return;
      }

      setError('');
      setFormData(prev => ({ ...prev, file }));
      setUploadStatus('success');
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validaciones
    if (!formData.title.trim()) {
      setError('El título es requerido');
      return;
    }

    if (!formData.subject.trim()) {
      setError('La asignatura es requerida');
      return;
    }

    if (!formData.level) {
      setError('El nivel es requerido');
      return;
    }

    if (!formData.file) {
      setError('Debes subir una presentación');
      return;
    }

    setIsLoading(true);
    setUploadStatus('uploading');

    try {
      // Crear FormData para enviar el archivo
      const formDataToSend = new FormData();
      formDataToSend.append('title', formData.title);
      formDataToSend.append('subject', formData.subject);
      formDataToSend.append('level', formData.level);
      formDataToSend.append('description', formData.description);
      formDataToSend.append('file', formData.file);

      // Llamar al backend
      await classesAPI.create(formDataToSend);

      setUploadStatus('success');

      // Redirigir a la página principal
      setTimeout(() => {
        navigate('/');
      }, 1000);
    } catch (err) {
      console.error('Error creating class:', err);
      setError(err.message || 'Error al crear la clase. Inténtalo de nuevo.');
      setUploadStatus('error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild>
              <Link to="/home">
                <ArrowLeft className="h-5 w-5" />
              </Link>
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Crear Nueva Clase</h1>
              <p className="text-sm text-gray-500">Completa la información de tu clase</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <form onSubmit={handleSubmit}>
          <div className="space-y-6">
            {/* Error Alert */}
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Basic Information Card */}
            <Card>
              <CardHeader>
                <CardTitle>Información Básica</CardTitle>
                <CardDescription>
                  Proporciona los detalles principales de la clase
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Title */}
                <div className="space-y-2">
                  <Label htmlFor="title">Título de la Clase *</Label>
                  <Input
                    id="title"
                    placeholder="Ej: Introducción a Algoritmos"
                    value={formData.title}
                    onChange={(e) => handleInputChange('title', e.target.value)}
                    required
                    disabled={isLoading}
                  />
                </div>

                {/* Subject */}
                <div className="space-y-2">
                  <Label htmlFor="subject">Asignatura *</Label>
                  <Input
                    id="subject"
                    placeholder="Ej: Ciencias de la Computación"
                    value={formData.subject}
                    onChange={(e) => handleInputChange('subject', e.target.value)}
                    required
                    disabled={isLoading}
                  />
                </div>

                {/* Level */}
                <div className="space-y-2">
                  <Label htmlFor="level">Nivel del Curso *</Label>
                  <Select
                    value={formData.level}
                    onValueChange={(value) => handleInputChange('level', value)}
                    disabled={isLoading}
                  >
                    <SelectTrigger id="level">
                      <SelectValue placeholder="Selecciona el nivel" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pregrado">Pregrado</SelectItem>
                      <SelectItem value="postgrado">Postgrado</SelectItem>
                      <SelectItem value="doctorado">Doctorado</SelectItem>
                      <SelectItem value="diplomado">Diplomado</SelectItem>
                      <SelectItem value="curso-corto">Curso Corto</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Description */}
                <div className="space-y-2">
                  <Label htmlFor="description">Descripción (opcional)</Label>
                  <Textarea
                    id="description"
                    placeholder="Describe brevemente el contenido de la clase..."
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    rows={4}
                    disabled={isLoading}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Upload Presentation Card */}
            <Card>
              <CardHeader>
                <CardTitle>Presentación</CardTitle>
                <CardDescription>
                  Sube tu archivo de presentación (PPTX máx. 50MB)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* File Input */}
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
                    <input
                      type="file"
                      id="file-upload"
                      accept=".pptx"
                      onChange={handleFileChange}
                      className="hidden"
                      disabled={isLoading}
                    />
                    <label
                      htmlFor="file-upload"
                      className="cursor-pointer flex flex-col items-center"
                    >
                      <Upload className="h-12 w-12 text-gray-400 mb-4" />
                      <span className="text-sm font-medium text-gray-700 mb-1">
                        Haz clic para subir o arrastra el archivo
                      </span>
                      <span className="text-xs text-gray-500">
                        PPTX (máx. 50MB)
                      </span>
                    </label>
                  </div>

                  {/* File Info */}
                  {formData.file && (
                    <div className="flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <FileText className="h-8 w-8 text-blue-600" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {formData.file.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {(formData.file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                      {uploadStatus === 'success' && (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      )}
                    </div>
                  )}

                  {/* Upload Status */}
                  {uploadStatus === 'uploading' && (
                    <Alert>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <AlertDescription>Procesando presentación...</AlertDescription>
                    </Alert>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Actions */}
            <div className="flex justify-end gap-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/home')}
                disabled={isLoading}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Crear Clase
              </Button>
            </div>
          </div>
        </form>
      </main>
    </div>
  );
};
