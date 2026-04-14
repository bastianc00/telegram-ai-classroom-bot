import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Plus,
  Search,
  BookOpen,
  Calendar,
  Play,
  MoreVertical,
  FileText,
  Clock,
  Loader2,
  LogOut,
  User
} from 'lucide-react';
import { classesAPI } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';

export const HomePage = () => {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadClasses();
  }, []);

  const loadClasses = async () => {
    try {
      setLoading(true);
      const data = await classesAPI.getAll();
      setClasses(data.classes || []);
      setError(null);
    } catch (err) {
      console.error('Error loading classes:', err);
      setError(err.message);
      setClasses([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredClasses = classes.filter(cls =>
    cls.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cls.subject.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleLogout = async () => {
    try {
      await signOut();
      navigate('/auth');
    } catch (error) {
      console.error('Error al cerrar sesión:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BookOpen className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Mis Clases</h1>
                <p className="text-sm text-gray-500">Gestiona tus presentaciones</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* User info */}
              <div className="flex items-center gap-2 text-sm">
                <User className="h-4 w-4 text-gray-600" />
                <span className="text-gray-700">{user?.email}</span>
              </div>

              {/* Logout button */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
              >
                <LogOut className="h-4 w-4 mr-2" />
                Cerrar Sesión
              </Button>

              {/* Nueva Clase button */}
              <Button asChild>
                <Link to="/classes/create">
                  <Plus className="mr-2 h-4 w-4" />
                  Nueva Clase
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Buscar clases por título o asignatura..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Loading State */}
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="ml-3 text-gray-600">Cargando clases...</span>
          </div>
        ) : (
          <>
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-blue-100 rounded-lg">
                      <BookOpen className="h-6 w-6 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Total Clases</p>
                      <p className="text-2xl font-bold">{classes.length}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-green-100 rounded-lg">
                      <FileText className="h-6 w-6 text-green-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Total Diapositivas</p>
                      <p className="text-2xl font-bold">
                        {classes.reduce((sum, cls) => sum + (cls.slides_count || 0), 0)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-purple-100 rounded-lg">
                      <Play className="h-6 w-6 text-purple-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Instancias Realizadas</p>
                      <p className="text-2xl font-bold">
                        {classes.reduce((sum, cls) => sum + (cls.instance_count || 0), 0)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Classes Grid */}
            {filteredClasses.length === 0 ? (
          <Card className="py-12">
            <CardContent>
              <div className="text-center">
                <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {searchTerm ? 'No se encontraron clases' : 'No tienes clases creadas'}
                </h3>
                <p className="text-gray-500 mb-4">
                  {searchTerm
                    ? 'Intenta con otros términos de búsqueda'
                    : 'Comienza creando tu primera clase'
                  }
                </p>
                {!searchTerm && (
                  <Button asChild>
                    <Link to="/classes/create">
                      <Plus className="mr-2 h-4 w-4" />
                      Crear Primera Clase
                    </Link>
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredClasses.map((classItem) => (
              <Card key={classItem.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg mb-2">{classItem.title}</CardTitle>
                      <CardDescription className="text-sm">
                        {classItem.subject}
                      </CardDescription>
                    </div>
                    <Button variant="ghost" size="icon">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="flex gap-2 mt-2">
                    <Badge variant="secondary">{classItem.level}</Badge>
                    <Badge variant="outline">
                      <FileText className="h-3 w-3 mr-1" />
                      {classItem.slides_count || 0} slides
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent className="space-y-2">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Calendar className="h-4 w-4" />
                    <span>Creada: {new Date(classItem.created_at).toLocaleDateString('es-ES')}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Clock className="h-4 w-4" />
                    <span>Actualizada: {new Date(classItem.updated_at).toLocaleDateString('es-ES')}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Play className="h-4 w-4" />
                    <span>{classItem.instance_count || 0} instancias realizadas</span>
                  </div>
                </CardContent>

                <CardFooter className="flex gap-2">
                  <Button asChild className="flex-1" size="sm">
                    <Link to={`/classes/${classItem.id}`}>
                      Ver Detalles
                    </Link>
                  </Button>
                  <Button asChild variant="outline" size="sm">
                    <Link to={`/classes/${classItem.id}/start`}>
                      <Play className="h-4 w-4" />
                    </Link>
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};
