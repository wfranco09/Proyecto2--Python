import { Droplets, ExternalLink } from "lucide-react";

interface FooterProps {
  lastSync: Date;
}

export const Footer = ({ lastSync }: FooterProps) => {
  return (
    <footer className="glass-card px-6 py-4 mt-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>Powered by</span>
          <span className="flex items-center gap-1 text-primary font-medium">
            <Droplets className="w-4 h-4" />
            rAIndrop AI
          </span>
        </div>
        
        <div className="flex items-center gap-6 text-xs">
          <a href="#" className="text-muted-foreground hover:text-primary transition-colors flex items-center gap-1">
            Metodología
            <ExternalLink className="w-3 h-3" />
          </a>
          <a href="#" className="text-muted-foreground hover:text-primary transition-colors flex items-center gap-1">
            API Docs
            <ExternalLink className="w-3 h-3" />
          </a>
          <a href="#" className="text-muted-foreground hover:text-primary transition-colors flex items-center gap-1">
            Contacto
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
        
        <div className="text-xs text-muted-foreground">
          <span>Powered by Meteosource</span>
          <span className="mx-2">|</span>
          <span>
            Última sincronización: {lastSync.toLocaleString('es-PA', {
              hour: '2-digit',
              minute: '2-digit',
              day: '2-digit',
              month: 'short'
            })}
          </span>
        </div>
      </div>
    </footer>
  );
};
