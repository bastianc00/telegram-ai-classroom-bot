import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  ChevronLeft,
  ChevronRight,
  X,
  Maximize2,
  Minimize2,
  Play,
  Pause,
  Clock,
  Grid3x3,
  Smartphone,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { classesAPI, instancesAPI, syncAPI } from '@/services/api';
import { useSocket } from '@/hooks/useSocket';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export const PresentationViewPage = () => {
  const { classId } = useParams();
  const navigate = useNavigate();
  const slideStartTimeRef = useRef(new Date());
  const currentSlideRef = useRef(0);
  const slidesRef = useRef([]);
  const checkSlidesIntervalRef = useRef(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [classData, setClassData] = useState(null);
  const [instance, setInstance] = useState(null);
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [slides, setSlides] = useState([]);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [showThumbnails, setShowThumbnails] = useState(false);
  const [startTime] = useState(new Date());
  const [elapsedTime, setElapsedTime] = useState(0);
  const [syncCode, setSyncCode] = useState('');
  const [slideFlow, setSlideFlow] = useState([1]);
  const [slideTimes, setSlideTimes] = useState({});
  const [newSlideNotification, setNewSlideNotification] = useState(null);

  // WebSocket connection
  const { isConnected, syncStatus, on, off } = useSocket(syncCode);

  // Initialize presentation: load class and create instance
  useEffect(() => {
    initializePresentation();
    return () => {
      // Cleanup check slides interval on unmount
      if (checkSlidesIntervalRef.current) {
        clearInterval(checkSlidesIntervalRef.current);
      }
    };
  }, [classId]);

  const initializePresentation = async () => {
    try {
      setLoading(true);

      // Load class data
      const classResponse = await classesAPI.getById(classId);
      setClassData(classResponse.class);

      // Load slides
      if (classResponse.class.slide_urls && classResponse.class.slide_urls.length > 0) {
        const slideData = classResponse.class.slide_urls.map((url, index) => ({
          id: index + 1,
          imageUrl: `${API_URL}${url}`,
          thumbnail: `${API_URL}${url}`
        }));
        setSlides(slideData);
        slidesRef.current = slideData; // Update ref for polling
      } else {
        setError('Esta clase no tiene slides cargados');
        return;
      }

      // Create instance
      const instanceResponse = await instancesAPI.create(classId);
      setInstance(instanceResponse.instance);
      setSyncCode(instanceResponse.instance.sync_code);

      // Start checking for new slides (AI generated)
      startCheckingNewSlides();

      setLoading(false);
    } catch (err) {
      console.error('Error initializing presentation:', err);
      setError(err.message || 'Error al iniciar la presentación');
      setLoading(false);
    }
  };

  // Check for new AI-generated slides periodically
  const startCheckingNewSlides = () => {
    checkSlidesIntervalRef.current = setInterval(async () => {
      try {
        const classResponse = await classesAPI.getById(classId);
        const currentSlidesCount = slidesRef.current.length;
        const newSlidesCount = classResponse.class.slides_count;

        if (newSlidesCount > currentSlidesCount) {
          // New slides were added!
          const slideData = classResponse.class.slide_urls.map((url, index) => ({
            id: index + 1,
            imageUrl: `${API_URL}${url}`,
            thumbnail: `${API_URL}${url}`
          }));

          setSlides(slideData);
          slidesRef.current = slideData;
          setClassData(classResponse.class);

          // Show notification
          const addedCount = newSlidesCount - currentSlidesCount;
          setNewSlideNotification(
            `${addedCount} nueva${addedCount > 1 ? 's' : ''} diapositiva${addedCount > 1 ? 's' : ''} generada${addedCount > 1 ? 's' : ''} por IA`
          );

          // Hide notification after 5 seconds
          setTimeout(() => setNewSlideNotification(null), 5000);
        }
      } catch (err) {
        // Silently ignore errors - this is a nice-to-have feature
        // Common in WSL/Docker environments
        if (err.message !== 'Failed to fetch') {
          console.error('Error checking new slides:', err);
        }
      }
    }, 5000); // Check every 5 seconds (reduced frequency to avoid WSL connection issues)
  };

  // WebSocket event listeners
  useEffect(() => {
    if (!on || !off) return;

    // Handle command events (pause/resume)
    const handleCommand = (data) => {
      console.log('[WebSocket] Command received:', data);
      const command = data.command;

      if (command === 'pause') {
        setIsPaused(true);
      } else if (command === 'resume') {
        setIsPaused(false);
      }
    };

    // Handle slide updates from Telegram bot
    const handleSlideUpdate = (data) => {
      console.log('[WebSocket] Slide update:', data);
      const backendSlide = data.slide_number - 1; // Convert to 0-indexed
      const frontendSlide = currentSlideRef.current;
      const slidesCount = slidesRef.current.length;

      if (backendSlide !== frontendSlide && backendSlide >= 0 && backendSlide < slidesCount) {
        changeSlide(backendSlide, false); // false = don't update backend (avoid loop)
      }
    };

    // Subscribe to events
    on('command', handleCommand);
    on('slide_update', handleSlideUpdate);

    // Cleanup on unmount
    return () => {
      off('command', handleCommand);
      off('slide_update', handleSlideUpdate);
    };
  }, [on, off]);

  // Track slide time
  const trackSlideTime = (slideNumber) => {
    const now = new Date();
    const timeSpent = Math.floor((now - slideStartTimeRef.current) / 1000);

    setSlideTimes(prev => {
      const updated = {
        ...prev,
        [slideNumber]: (prev[slideNumber] || 0) + timeSpent
      };
      return updated;
    });

    slideStartTimeRef.current = now;
  };

  const changeSlide = async (newIndex, updateBackend = true) => {
    const slidesCount = slidesRef.current.length;
    const currentIndex = currentSlideRef.current;

    if (newIndex >= 0 && newIndex < slidesCount && newIndex !== currentIndex) {
      // Track time on current slide
      trackSlideTime(currentIndex + 1);

      // Update slide flow
      setSlideFlow(prev => [...prev, newIndex + 1]);

      // Change slide
      setCurrentSlideIndex(newIndex);
      currentSlideRef.current = newIndex; // Update ref for polling

      // Update backend if synced and not coming from bot
      if (updateBackend && syncCode) {
        try {
          await syncAPI.updateSlide(syncCode, newIndex + 1);
        } catch (err) {
          console.error('Error updating backend slide:', err);
        }
      }
    }
  };

  // Timer
  useEffect(() => {
    if (!isPaused) {
      const timer = setInterval(() => {
        const elapsed = Math.floor((new Date() - startTime) / 1000);
        setElapsedTime(elapsed);
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [isPaused, startTime]);

  // Listen for fullscreen changes (when user presses ESC)
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault();
        nextSlide();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        previousSlide();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [currentSlideIndex, slides.length]);

  const nextSlide = () => {
    if (currentSlideIndex < slides.length - 1) {
      changeSlide(currentSlideIndex + 1);
    }
  };

  const previousSlide = () => {
    if (currentSlideIndex > 0) {
      changeSlide(currentSlideIndex - 1);
    }
  };

  const goToSlide = (index) => {
    changeSlide(index);
    setShowThumbnails(false);
  };

  const toggleFullscreen = async () => {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (err) {
      console.error('Error toggling fullscreen:', err);
    }
  };

  const handleEndClass = async () => {
    if (!confirm('¿Estás seguro de que quieres finalizar la clase?')) {
      return;
    }

    try {
      // Stop polling first
      if (checkSlidesIntervalRef.current) {
        clearInterval(checkSlidesIntervalRef.current);
      }

      // Calculate final slide time
      const now = new Date();
      const finalSlideTime = Math.floor((now - slideStartTimeRef.current) / 1000);
      const currentSlide = currentSlideIndex + 1;

      // Create updated slide times with final slide
      const updatedSlideTimes = {
        ...slideTimes,
        [currentSlide]: (slideTimes[currentSlide] || 0) + finalSlideTime
      };

      // Prepare data to send to backend
      const endData = {
        slide_flow: slideFlow,
        slide_times: updatedSlideTimes
      };

      // End instance with slide data
      await instancesAPI.end(classId, instance.id, endData);

      // Navigate to class detail
      navigate(`/classes/${classId}`);
    } catch (err) {
      console.error('Error ending class:', err);
      alert('Error al finalizar la clase. Por favor intenta nuevamente.');
    }
  };

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center text-white">
          <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-blue-400" />
          <p className="text-lg">Cargando presentación...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900 p-4">
        <Alert variant="destructive" className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error}
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/classes/${classId}`)}
              className="mt-4 w-full"
            >
              Volver a la clase
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* AI Slide Notification */}
      {newSlideNotification && (
        <div className="fixed top-20 right-6 z-50 animate-in slide-in-from-right duration-300">
          <Alert className="bg-gradient-to-r from-purple-600 to-blue-600 border-0 shadow-2xl min-w-[320px]">
            <AlertDescription className="flex items-center gap-3 text-white">
              <div className="flex-shrink-0 w-10 h-10 bg-white bg-opacity-20 rounded-full flex items-center justify-center animate-pulse">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="font-bold text-sm">Nueva diapositiva generada</p>
                <p className="text-xs text-white text-opacity-90 mt-1">{newSlideNotification}</p>
              </div>
              <button
                onClick={() => setNewSlideNotification(null)}
                className="flex-shrink-0 hover:bg-white hover:bg-opacity-20 rounded-full p-1 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Header Controls */}
      <div className="fixed top-0 left-0 right-0 z-50 bg-gray-800 border-b border-gray-700 px-6 py-3">
        <div className="flex items-center justify-between">
          {/* Left: Navigation & Info */}
                <div className="flex items-center gap-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleEndClass}
                  className="text-white hover:text-red-400"
                >
                  <X className="h-5 w-5 mr-2" />
                  Finalizar
                </Button>

                <div className="h-6 w-px bg-gray-600" />

                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="bg-gray-700 text-white">
                  Slide {currentSlideIndex + 1} / {slides.length}
                  </Badge>
                  <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsPaused(!isPaused)}
                  className="text-white"
                  >
                  {isPaused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
                  </Button>
                  <div className="flex items-center gap-2 text-sm">
                  <Clock className="h-4 w-4" />
                  <span className="font-mono">{formatTime(elapsedTime)}</span>
                  </div>
                </div>
                </div>

                {/* Center: Sync Code */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-4 py-2 bg-gray-700 rounded-lg">
              <Smartphone className="h-4 w-4 text-blue-400" />
              <span className="text-sm text-gray-300">Código:</span>
              <span className="font-mono font-bold text-lg text-blue-400">{syncCode}</span>
            </div>
          </div>

          {/* Right: View Controls */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowThumbnails(!showThumbnails)}
              className="text-white"
            >
              <Grid3x3 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleFullscreen}
              className="text-white"
            >
              {isFullscreen ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Main Presentation Area */}
      <div className="pt-16 pb-20 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Slide Display */}
          <div className="relative aspect-video bg-black rounded-lg overflow-hidden shadow-2xl">
            <img
              src={slides[currentSlideIndex]?.imageUrl}
              alt={`Slide ${currentSlideIndex + 1}`}
              className="w-full h-full object-contain"
            />

            {/* Pause Overlay */}
            {isPaused && (
              <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                <div className="text-center">
                  <Pause className="h-16 w-16 mx-auto mb-4" />
                  <p className="text-xl font-semibold">Presentación en pausa</p>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <button
              onClick={previousSlide}
              disabled={currentSlideIndex === 0}
              className="absolute left-4 top-1/2 -translate-y-1/2 p-3 bg-black bg-opacity-50 hover:bg-opacity-75 rounded-full disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              <ChevronLeft className="h-8 w-8" />
            </button>

            <button
              onClick={nextSlide}
              disabled={currentSlideIndex === slides.length - 1}
              className="absolute right-4 top-1/2 -translate-y-1/2 p-3 bg-black bg-opacity-50 hover:bg-opacity-75 rounded-full disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              <ChevronRight className="h-8 w-8" />
            </button>
          </div>

          {/* Thumbnails Grid Overlay */}
          {showThumbnails && (
            <div className="fixed inset-0 z-40 bg-black bg-opacity-90 flex items-center justify-center p-8">
              <div className="w-full max-w-6xl max-h-[80vh] overflow-y-auto">
                <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 p-4">
                  {slides.map((slide, index) => (
                    <button
                      key={slide.id}
                      onClick={() => goToSlide(index)}
                      className={`relative aspect-video rounded-lg overflow-hidden border-2 transition-all hover:scale-105 ${
                        index === currentSlideIndex
                          ? 'border-blue-500 ring-2 ring-blue-400'
                          : 'border-gray-600 hover:border-blue-400'
                      }`}
                    >
                      <img
                        src={slide.thumbnail}
                        alt={`Slide ${index + 1}`}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-75 px-2 py-1">
                        <span className="text-xs font-medium">{index + 1}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Progress Bar */}
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-gray-800 border-t border-gray-700 px-6 py-3">
        <div className="flex items-center gap-4">
          {/* Progress Bar */}
          <div className="flex-1">
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{
                  width: `${((currentSlideIndex + 1) / slides.length) * 100}%`
                }}
              />
            </div>
          </div>

          {/* Navigation Buttons */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={previousSlide}
              disabled={currentSlideIndex === 0}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Anterior
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={nextSlide}
              disabled={currentSlideIndex === slides.length - 1}
            >
              Siguiente
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
