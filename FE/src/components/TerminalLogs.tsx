import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Terminal, Copy, Trash2 } from 'lucide-react';

interface TerminalLogsProps {
  logs: string[];
  isProcessing?: boolean;
}

export const TerminalLogs = ({ logs, isProcessing = false }: TerminalLogsProps) => {
  const logsEndRef = useRef<HTMLDivElement>(null);
  const [autoscroll, setAutoscroll] = useState(true);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoscroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoscroll]);

  const handleCopy = () => {
    const logText = logs.join('\n');
    navigator.clipboard.writeText(logText);
  };

  const getLogColor = (log: string): string => {
    // Colorize based on log content
    if (log.includes('✓') || log.includes('✅') || log.includes('Success') || log.includes('complete')) {
      return 'text-green-400';
    }
    if (log.includes('❌') || log.includes('Error') || log.includes('failed')) {
      return 'text-red-400';
    }
    if (log.includes('⚠️') || log.includes('Warning') || log.includes('skipped')) {
      return 'text-yellow-400';
    }
    if (log.includes('Strategy') || log.includes('confidence')) {
      return 'text-cyan-400';
    }
    if (log.includes('Found page number') || log.includes('Detected')) {
      return 'text-purple-400';
    }
    if (log.includes('Testing') || log.includes('Extracting') || log.includes('Rebuilding')) {
      return 'text-blue-400';
    }
    return 'text-gray-300';
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-primary" />
            <div>
              <CardTitle>Backend Terminal Logs</CardTitle>
              <CardDescription>
                {isProcessing ? 'Processing...' : `${logs.length} log entries`}
              </CardDescription>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              disabled={logs.length === 0}
            >
              <Copy className="w-4 h-4 mr-2" />
              Copy
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div 
          className="bg-gray-900 rounded-lg p-4 font-mono text-sm overflow-auto"
          style={{ maxHeight: '600px' }}
        >
          {logs.length === 0 ? (
            <div className="text-gray-500 text-center py-8">
              {isProcessing ? (
                <>
                  <div className="animate-pulse">Processing...</div>
                  <div className="text-xs mt-2">Logs will appear here</div>
                </>
              ) : (
                'Upload a PDF to see processing logs'
              )}
            </div>
          ) : (
            <div className="space-y-1">
              {logs.map((log, index) => (
                <div key={index} className={`${getLogColor(log)} break-words`}>
                  <span className="text-gray-600 mr-2">{String(index + 1).padStart(3, '0')}</span>
                  {log}
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          )}
          
          {isProcessing && logs.length > 0 && (
            <div className="text-yellow-400 animate-pulse mt-2">
              ▶ Processing...
            </div>
          )}
        </div>
        
        {logs.length > 10 && (
          <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoscroll}
                onChange={(e) => setAutoscroll(e.target.checked)}
                className="rounded"
              />
              Auto-scroll to bottom
            </label>
            <span>{logs.length} lines</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};