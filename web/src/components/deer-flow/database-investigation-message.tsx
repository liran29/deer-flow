// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

import { useTranslations } from "next-intl";
import { useMemo } from "react";

import { Markdown } from "./markdown";

export interface DatabaseInvestigationMessageProps {
  content: string;
}

export function DatabaseInvestigationMessage({ content }: DatabaseInvestigationMessageProps) {
  const t = useTranslations("chat.inputBox.databaseInvestigation");
  
  const processedContent = useMemo(() => {
    // Handle different message templates
    if (content === "__DB_INVESTIGATION_NO_DATABASE__") {
      return t("noDatabase");
    }
    
    if (content.startsWith("__DB_INVESTIGATION_STARTING__|")) {
      const topic = content.split("|")[1] || "";
      return `${t("starting")}\n${t("analyzing", { topic })}`;
    }
    
    if (content.startsWith("__DB_INVESTIGATION_COMPLETED__|")) {
      const parts = content.split("|");
      const analysis = parts[1] || "";
      const dbCount = parts[2] || "0";
      
      return `${t("completed")}

## ${t("analysisRecommendations")}
${analysis}

## ${t("databaseResources")}
${t("resourcesSummary", { count: dbCount })}

${t("guidanceNote")}`;
    }
    
    if (content.startsWith("__DB_INVESTIGATION_FAILED__|")) {
      const error = content.split("|")[1] || "Unknown error";
      return t("failed", { error });
    }
    
    // Fallback to original content
    return content;
  }, [content, t]);

  return (
    <div className="database-investigation-message">
      <Markdown animated>{processedContent}</Markdown>
    </div>
  );
}