import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Box,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Divider,
  Stack
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  VolumeUp,
  Refresh,
  SmartToy,
  RecordVoiceOver,
  NewspaperOutlined
} from '@mui/icons-material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import axios from 'axios';
import './App.css';

// Create a beautiful theme for News Breeze
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 12,
  },
});

interface Article {
  title: string;
  summary: string;
  ai_summary?: string;
  url: string;
  source: string;
  published_date: string;
  has_audio: boolean;
  audio_url?: string;
  voice_synthesis_metadata?: {
    success: boolean;
    voice_name: string;
    voice_description: string;
    celebrity_voice: string;
  };
}

interface NewsResponse {
  success: boolean;
  articles: Article[];
  total_articles: number;
  processing_time: number;
  voice_synthesis_enabled: boolean;
}

const CELEBRITY_VOICES = {
  morgan_freeman: 'Morgan Freeman Style',
  david_attenborough: 'David Attenborough Style',
  news_anchor_pro: 'Professional News Anchor',
  friendly_host: 'Friendly Talk Show Host',
  dramatic_narrator: 'Dramatic Movie Narrator',
  tech_reviewer: 'Tech Reviewer Style'
};

function App() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedVoice, setSelectedVoice] = useState('morgan_freeman');
  const [playingAudio, setPlayingAudio] = useState<string | null>(null);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);

  const API_BASE = 'http://localhost:8000';

  const fetchNews = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post<NewsResponse>(`${API_BASE}/news`, {
        max_articles: 6,
        voice: selectedVoice
      });
      
      if (response.data.success) {
        setArticles(response.data.articles);
      } else {
        setError('Failed to fetch news articles');
      }
    } catch (err) {
      setError('Unable to connect to News Breeze API. Make sure the backend is running on localhost:8000');
      console.error('API Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const playAudio = (audioUrl: string, articleTitle: string) => {
    // Stop current audio if playing
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
    }

    if (playingAudio === audioUrl) {
      setPlayingAudio(null);
      setCurrentAudio(null);
      return;
    }

    const audio = new Audio(`${API_BASE}${audioUrl}`);
    audio.onended = () => {
      setPlayingAudio(null);
      setCurrentAudio(null);
    };
    audio.onerror = () => {
      setError(`Failed to play audio for: ${articleTitle}`);
      setPlayingAudio(null);
      setCurrentAudio(null);
    };

    audio.play();
    setPlayingAudio(audioUrl);
    setCurrentAudio(audio);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  useEffect(() => {
    fetchNews();
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, minHeight: '100vh', backgroundColor: 'background.default' }}>
        {/* Header */}
        <AppBar position="static" elevation={0} sx={{ background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)' }}>
          <Toolbar>
            <NewspaperOutlined sx={{ mr: 2, fontSize: 32 }} />
            <Typography variant="h4" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
              News Breeze
            </Typography>
            <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
              AI-Powered News with Celebrity Voices
            </Typography>
          </Toolbar>
        </AppBar>

        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
          {/* Controls */}
          <Paper elevation={2} sx={{ p: 3, mb: 4, borderRadius: 3 }}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} alignItems="center">
              <FormControl sx={{ minWidth: 300 }}>
                <InputLabel>Celebrity Voice Style</InputLabel>
                <Select
                  value={selectedVoice}
                  label="Celebrity Voice Style"
                  onChange={(e) => setSelectedVoice(e.target.value)}
                  startAdornment={<RecordVoiceOver sx={{ mr: 1, color: 'primary.main' }} />}
                >
                  {Object.entries(CELEBRITY_VOICES).map(([key, name]) => (
                    <MenuItem key={key} value={key}>
                      {name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <Button
                variant="contained"
                size="large"
                onClick={fetchNews}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <Refresh />}
                sx={{ height: 56, borderRadius: 2, minWidth: 200 }}
              >
                {loading ? 'Loading News...' : 'Refresh News'}
              </Button>
            </Stack>
          </Paper>

          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
              {error}
            </Alert>
          )}

          {/* News Articles */}
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { 
              xs: '1fr', 
              md: 'repeat(2, 1fr)', 
              lg: 'repeat(3, 1fr)' 
            }, 
            gap: 3 
          }}>
            {articles.map((article, index) => (
              <Card 
                key={index}
                elevation={3} 
                sx={{ 
                  height: '100%', 
                  display: 'flex', 
                  flexDirection: 'column',
                  borderRadius: 3,
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 6
                  }
                }}
              >
                <CardContent sx={{ flexGrow: 1, p: 3 }}>
                  {/* Source and Date */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Chip 
                      label={article.source} 
                      size="small" 
                      color="primary" 
                      variant="outlined"
                    />
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(article.published_date)}
                    </Typography>
                  </Box>

                  {/* Title */}
                  <Typography variant="h6" component="h2" gutterBottom sx={{ fontWeight: 600, lineHeight: 1.3 }}>
                    {article.title}
                  </Typography>

                  <Divider sx={{ my: 2 }} />

                  {/* AI Summary */}
                  {article.ai_summary && (
                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <SmartToy sx={{ fontSize: 16, mr: 1, color: 'primary.main' }} />
                        <Typography variant="caption" color="primary" fontWeight="bold">
                          AI Summary
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.5 }}>
                        {article.ai_summary}
                      </Typography>
                    </Box>
                  )}

                  {/* Voice Synthesis Info */}
                  {article.voice_synthesis_metadata && article.voice_synthesis_metadata.success && (
                    <Box sx={{ mt: 2 }}>
                      <Chip
                        icon={<VolumeUp />}
                        label={article.voice_synthesis_metadata.voice_name}
                        size="small"
                        color="secondary"
                        variant="outlined"
                      />
                    </Box>
                  )}
                </CardContent>

                <CardActions sx={{ p: 3, pt: 0 }}>
                  <Stack direction="row" spacing={1} sx={{ width: '100%' }}>
                    {/* Play Audio Button */}
                    {article.has_audio && article.audio_url && (
                      <Button
                        variant="contained"
                        size="small"
                        onClick={() => playAudio(article.audio_url!, article.title)}
                        startIcon={playingAudio === article.audio_url ? <Pause /> : <PlayArrow />}
                        color={playingAudio === article.audio_url ? "secondary" : "primary"}
                        sx={{ borderRadius: 2, flex: 1 }}
                      >
                        {playingAudio === article.audio_url ? 'Pause' : 'Play'}
                      </Button>
                    )}
                    
                    {/* Read Full Article */}
                    <Button
                      variant="outlined"
                      size="small"
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      sx={{ borderRadius: 2, flex: 1 }}
                    >
                      Read Full
                    </Button>
                  </Stack>
                </CardActions>
              </Card>
            ))}
          </Box>

          {/* Loading State */}
          {loading && articles.length === 0 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
              <Box sx={{ textAlign: 'center' }}>
                <CircularProgress size={60} sx={{ mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Loading latest news with AI summaries...
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Generating {CELEBRITY_VOICES[selectedVoice as keyof typeof CELEBRITY_VOICES]} voice synthesis
                </Typography>
              </Box>
            </Box>
          )}

          {/* Empty State */}
          {!loading && articles.length === 0 && !error && (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <NewspaperOutlined sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h5" color="text.secondary" gutterBottom>
                No news articles available
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Click "Refresh News" to fetch the latest articles
              </Typography>
            </Box>
          )}
        </Container>

        {/* Footer */}
        <Box sx={{ bgcolor: 'primary.main', color: 'white', py: 3, mt: 6 }}>
          <Container maxWidth="lg">
            <Typography variant="body2" align="center">
              News Breeze - AI-Powered News Aggregation with Celebrity Voice Synthesis
            </Typography>
            <Typography variant="caption" align="center" display="block" sx={{ mt: 1, opacity: 0.8 }}>
              Powered by AI Summarization & Text-to-Speech Technology
            </Typography>
          </Container>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;
