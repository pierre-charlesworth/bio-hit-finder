import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Menu, X, Upload, CheckCircle, AlertCircle, Database } from 'lucide-react';

interface HeaderProps {
  dataStatus?: 'none' | 'uploaded' | 'sample' | 'processing' | 'error';
  fileName?: string;
}

const Header = ({ dataStatus = 'none', fileName }: HeaderProps) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const navItems = [
    { label: 'Work', href: '#work' },
    { label: 'About', href: '#about' },
    { label: 'Contact', href: '#contact' },
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

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm border-b border-border">
      <div className="container-fluid max-w-7xl mx-auto">
        <div className="flex items-center justify-between py-4">
          {/* Data Status */}
          <div className="flex items-center">
            {getDataStatusBadge()}
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            {navItems.map((item) => (
              <a
                key={item.label}
                href={item.href}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200"
              >
                {item.label}
              </a>
            ))}
          </nav>

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </Button>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <nav className="md:hidden py-4 border-t border-border">
            <div className="flex flex-col space-y-4">
              {navItems.map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200"
                  onClick={() => setIsMenuOpen(false)}
                >
                  {item.label}
                </a>
              ))}
            </div>
          </nav>
        )}
      </div>
    </header>
  );
};

export default Header;