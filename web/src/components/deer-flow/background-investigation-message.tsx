// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

import { useMemo } from "react";

import { Markdown } from "./markdown";

export interface BackgroundInvestigationMessageProps {
  content: string;
}

export function BackgroundInvestigationMessage({ content }: BackgroundInvestigationMessageProps) {
  const processedContent = useMemo(() => {
    // Process raw content that may contain [SOURCE] links
    // Extract source links from content and format them as markdown links
    // Handle multiple formats: [SOURCE] URL or [SOURCE] [URL] or [SOURCE] [\nURL\n]
    const sourceRegex = /\[SOURCE\]\s*(?:\[?\s*)?(https?:\/\/[^\s\]]+)(?:\s*\])?/g;
    let processedContent = content;
    const sources: string[] = [];
    let match;
    
    // Extract all source URLs
    while ((match = sourceRegex.exec(content)) !== null) {
      if (match[1]) {
        sources.push(match[1]);
      }
    }
    
    // Remove [SOURCE] markers from content and add reference links at the end
    processedContent = content.replace(sourceRegex, '').trim();
    
    // Add source references if found
    if (sources.length > 0) {
      processedContent += '\n\n**Source(s):**\n';
      sources.forEach((url, index) => {
        try {
          // Get the domain name from the URL for display
          const urlObj = new URL(url);
          const domain = urlObj.hostname.replace('www.', '');
          processedContent += `- [${domain}](${url})\n`;
        } catch (e) {
          // If URL parsing fails, use the raw URL
          processedContent += `- [Link ${index + 1}](${url})\n`;
        }
      });
    }
    
    return processedContent;
  }, [content]);

  return (
    <div className="background-investigation-message">
      <Markdown animated>{processedContent}</Markdown>
    </div>
  );
}