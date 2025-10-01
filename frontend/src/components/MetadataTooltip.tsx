import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./ui/tooltip";

interface Message {
  created_at?: string;
  model?: string | null;
  token_in?: number | null;
  token_out?: number | null;
  cost_usd?: string | number | null;
  api_calls?: number | null;
  agents?: { activated?: string[]; count?: number } | null;
  tools?: { used?: string[]; count?: number } | null;
  metadata?: Record<string, any> | null;
}

interface MetadataTooltipProps {
  message: Message;
}

export function MetadataTooltip({ message }: MetadataTooltipProps) {
  const info: string[] = [];

  if (message.created_at) {
    info.push(`Time: ${new Date(message.created_at).toLocaleString()}`);
  }

  const modelComputed = message.model || (message.metadata && message.metadata.provider 
    ? `${message.metadata.provider}${message.model ? `:${message.model}` : ''}` 
    : '');
  if (modelComputed) {
    info.push(`Model: ${modelComputed}`);
  }

  if (message.token_in != null || message.token_out != null) {
    info.push(`Tokens: ${message.token_in || 0} in / ${message.token_out || 0} out`);
  }

  if (message.cost_usd != null) {
    info.push(`Cost: $${message.cost_usd}`);
  }

  if (message.api_calls != null) {
    info.push(`API Calls: ${message.api_calls}`);
  }

  const agentNames = message.agents?.activated || [];
  const agentCount = message.agents?.count ?? agentNames.length;
  if (agentCount > 0) {
    info.push(`Agents: ${agentCount}${agentNames.length ? ` (${agentNames.join(', ')})` : ''}`);
  }

  const toolNames = message.tools?.used || [];
  const toolCount = message.tools?.count ?? toolNames.length;
  if (toolCount > 0) {
    info.push(`Tools: ${toolCount}${toolNames.length ? ` (${toolNames.join(', ')})` : ''}`);
  }

  if (info.length === 0) {
    return null;
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button 
            className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-muted hover:bg-muted/80 text-muted-foreground text-xs font-medium transition-colors"
            aria-label="Message metadata"
          >
            i
          </button>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          <div className="space-y-1 text-xs">
            {info.map((item, idx) => (
              <div key={idx}>{item}</div>
            ))}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
