import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Menu, X, Upload, CheckCircle, AlertCircle, Database, Circle, Play } from 'lucide-react';

interface HeaderProps {
  dataStatus?: 'none' | 'uploaded' | 'sample' | 'processing' | 'error';
  fileName?: string;
  backendStatus?: 'connected' | 'connecting' | 'error';
  onProcessData?: () => void;
  canProcess?: boolean;
  isProcessing?: boolean;
}

const Header = ({ 
  dataStatus = 'none', 
  fileName, 
  backendStatus = 'connected',
  onProcessData,
  canProcess = false,
  isProcessing = false
}: HeaderProps) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const navItems = [
    { label: 'Home', href: '/' },
    { label: 'Analysis', href: '/analysis' },
    { label: 'Rationale', href: '/rationale' },
  ];

  const getDataStatusBadge = () => {
    switch (dataStatus) {
      case 'error':
        return <Badge variant="destructive" className="gap-1"><AlertCircle className="h-3 w-3" />Failed</Badge>;
      case 'processing':
        return <Badge variant="secondary" className="gap-1">Processing...</Badge>;
      case 'uploaded':
        return <Badge variant="secondary" className="gap-1"><CheckCircle className="h-3 w-3" />{fileName || 'Ready'}</Badge>;
      case 'sample':
        return <Badge variant="secondary" className="gap-1"><Database className="h-3 w-3" />Sample Data</Badge>;
      default:
        return <Badge variant="outline" className="gap-1"><Upload className="h-3 w-3" />No Data</Badge>;
    }
  };

  const getBackendStatusBadge = () => {
    switch (backendStatus) {
      case 'error':
        return <Badge variant="destructive" className="gap-1"><Circle className="w-2 h-2 fill-red-500" />Disconnected</Badge>;
      case 'connecting':
        return <Badge variant="secondary" className="gap-1"><Circle className="w-2 h-2 fill-yellow-500" />Connecting...</Badge>;
      default:
        return <Badge variant="default" className="gap-1"><Circle className="w-2 h-2 fill-green-500" />Connected</Badge>;
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm border-b border-border">
      <div className="container-fluid max-w-7xl mx-auto">
        <div className="flex items-center justify-between py-4">
          {/* Left Side - Status Indicators */}
          <div className="flex items-center gap-3">
            {getDataStatusBadge()}
            {getBackendStatusBadge()}
          </div>

          {/* Center - Process Button */}
          <div className="flex items-center">
            <div 
              className={`transition-all duration-300 ease-in-out ${
                canProcess 
                  ? 'opacity-100 scale-100 translate-y-0' 
                  : 'opacity-0 scale-95 translate-y-1 pointer-events-none'
              }`}
            >
              <Button 
                size="sm" 
                className="gap-1"
                onClick={onProcessData}
                disabled={isProcessing}
              >
                <Play className="h-3 w-3" />
                {isProcessing ? 'Processing...' : 'Process'}
              </Button>
            </div>
          </div>

          {/* Right Side - Navigation */}
          <div className="flex items-center">
            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-8">
              {navItems.map((item) => (
                <Link
                  key={item.label}
                  to={item.href}
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200"
                >
                  {item.label}
                </Link>
              ))}
            </nav>

            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden ml-4"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
            >
              {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <nav className="md:hidden py-4 border-t border-border">
            <div className="flex flex-col space-y-4">
              {navItems.map((item) => (
                <Link
                  key={item.label}
                  to={item.href}
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200"
                  onClick={() => setIsMenuOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </nav>
        )}
      </div>
    </header>
  );
};

export default Header;