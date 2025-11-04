import { useState } from 'react';
import { FileText, CheckCircle, TrendingUp, Loader2, ChevronDown, ChevronRight, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Button } from '@/components/ui/button';

export interface Strategy {
  name: string;
  confidence: number;
  details: string;
}

export interface ProcessingResult {
  strategies: Strategy[];
  selectedStrategy: {
    name: string;
    confidence: number;
  };
  pageMapping: {
    original: number[];
    final: number[];
  };
  reasoning?: string;
  metadata?: {
    original_filename?: string;
    page_count?: number;
    initial_order?: number[];
    final_order?: number[];
    confidences?: number[];
    summaries?: { [key: number]: string };
  };
}

interface ProcessingLogsProps {
  result?: ProcessingResult;
  isProcessing: boolean;
}

export const ProcessingLogs = ({ result, isProcessing }: ProcessingLogsProps) => {
  const [expandedSections, setExpandedSections] = useState({
    ordering: true,
    confidence: true,
    preview: true,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.8) return 'text-green-600';
    if (conf >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceBg = (conf: number) => {
    if (conf >= 0.8) return 'bg-green-500';
    if (conf >= 0.6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (isProcessing) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-primary" />
            <CardTitle>Processing PDF...</CardTitle>
          </div>
          <CardDescription>Analyzing document structure and determining optimal page order</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (!result) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Waiting for Upload</CardTitle>
          <CardDescription>Upload a shuffled PDF to begin processing</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const metadata = result.metadata;
  const avgConfidence = metadata?.confidences 
    ? metadata.confidences.reduce((a, b) => a + b, 0) / metadata.confidences.length 
    : result.selectedStrategy.confidence;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <CardTitle>Reconstruction Complete</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-3 bg-primary/10 rounded-lg">
              <p className="text-sm text-muted-foreground mb-1">Total Pages</p>
              <p className="text-2xl font-bold">{metadata?.page_count || result.pageMapping.final.length}</p>
            </div>
            <div className="text-center p-3 bg-green-500/10 rounded-lg">
              <p className="text-sm text-muted-foreground mb-1">Avg Confidence</p>
              <p className={`text-2xl font-bold ${getConfidenceColor(avgConfidence)}`}>
                {(avgConfidence * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Page Ordering */}
      <Card>
        <Collapsible open={expandedSections.ordering} onOpenChange={() => toggleSection('ordering')}>
          <CardHeader>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" className="w-full justify-between p-0 h-auto hover:bg-transparent">
                <CardTitle>Page Ordering</CardTitle>
                {expandedSections.ordering ? (
                  <ChevronDown className="w-5 h-5 text-muted-foreground" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-muted-foreground" />
                )}
              </Button>
            </CollapsibleTrigger>
          </CardHeader>
          <CollapsibleContent>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium mb-2">Initial Order (first 15):</p>
                <div className="flex flex-wrap gap-1">
                  {(metadata?.initial_order || result.pageMapping.original).slice(0, 15).map((page, idx) => (
                    <Badge key={idx} variant="outline" className="font-mono">
                      {page}
                    </Badge>
                  ))}
                  {(metadata?.initial_order || result.pageMapping.original).length > 15 && (
                    <span className="text-sm text-muted-foreground">...</span>
                  )}
                </div>
              </div>
              
              <div className="flex items-center justify-center py-2">
                <ArrowRight className="w-5 h-5 text-primary" />
              </div>

              <div>
                <p className="text-sm font-medium mb-2">Final Order (first 15):</p>
                <div className="flex flex-wrap gap-1">
                  {(metadata?.final_order || result.pageMapping.final).slice(0, 15).map((page, idx) => (
                    <Badge key={idx} variant="default" className="font-mono">
                      {page}
                    </Badge>
                  ))}
                  {(metadata?.final_order || result.pageMapping.final).length > 15 && (
                    <span className="text-sm text-muted-foreground">...</span>
                  )}
                </div>
              </div>
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      </Card>

      {/* Confidence Analysis */}
      {metadata?.confidences && (
        <Card>
          <Collapsible open={expandedSections.confidence} onOpenChange={() => toggleSection('confidence')}>
            <CardHeader>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" className="w-full justify-between p-0 h-auto hover:bg-transparent">
                  <CardTitle>Confidence Analysis</CardTitle>
                  {expandedSections.confidence ? (
                    <ChevronDown className="w-5 h-5 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-muted-foreground" />
                  )}
                </Button>
              </CollapsibleTrigger>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center p-3 bg-green-500/10 rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1">High (≥80%)</p>
                    <p className="text-xl font-bold text-green-600">
                      {metadata.confidences.filter(c => c >= 0.8).length}
                    </p>
                  </div>
                  <div className="text-center p-3 bg-yellow-500/10 rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1">Medium (60-80%)</p>
                    <p className="text-xl font-bold text-yellow-600">
                      {metadata.confidences.filter(c => c >= 0.6 && c < 0.8).length}
                    </p>
                  </div>
                  <div className="text-center p-3 bg-red-500/10 rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1">Low (&lt;60%)</p>
                    <p className="text-xl font-bold text-red-600">
                      {metadata.confidences.filter(c => c < 0.6).length}
                    </p>
                  </div>
                </div>

                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {metadata.confidences.slice(0, 10).map((conf, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <span className="text-sm text-muted-foreground w-24 flex-shrink-0">
                        {metadata.final_order?.[idx]} → {metadata.final_order?.[idx + 1] || 'End'}
                      </span>
                      <Progress value={conf * 100} className="h-6 flex-1" indicatorClassName={getConfidenceBg(conf)} />
                      <span className={`text-sm font-medium ${getConfidenceColor(conf)} w-12 text-right flex-shrink-0`}>
                        {(conf * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                  {metadata.confidences.length > 10 && (
                    <p className="text-sm text-muted-foreground text-center pt-2">
                      Showing first 10 of {metadata.confidences.length} transitions
                    </p>
                  )}
                </div>
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>
      )}

      {/* Page Content Preview */}
      {metadata?.summaries && (
        <Card>
          <Collapsible open={expandedSections.preview} onOpenChange={() => toggleSection('preview')}>
            <CardHeader>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" className="w-full justify-between p-0 h-auto hover:bg-transparent">
                  <CardTitle>Page Content Preview</CardTitle>
                  {expandedSections.preview ? (
                    <ChevronDown className="w-5 h-5 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-muted-foreground" />
                  )}
                </Button>
              </CollapsibleTrigger>
            </CardHeader>
            <CollapsibleContent>
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {metadata.final_order?.slice(0, 8).map((pageIdx, position) => (
                    <div key={position} className="border-l-4 border-primary pl-4 py-2 bg-muted/50 rounded-r">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm font-bold text-primary">Position {position}</span>
                        <span className="text-xs text-muted-foreground">(Original page {pageIdx})</span>
                        {metadata.confidences?.[position] && (
                          <Badge variant="secondary" className={getConfidenceColor(metadata.confidences[position])}>
                            {(metadata.confidences[position] * 100).toFixed(0)}%
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {metadata.summaries[pageIdx]?.substring(0, 150).replace(/\n/g, ' ')}
                        {metadata.summaries[pageIdx]?.length > 150 ? '...' : ''}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>
      )}
    </div>
  );
};
