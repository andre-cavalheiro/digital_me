"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { Loader2, MessageSquarePlus, Plus, RotateCw, Send } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"
import { createDocumentConversation, fetchDocumentConversations } from "@/lib/api/conversations"
import { fetchMessages, sendMessage, subscribeToAssistantStream, type AssistantStreamEvent } from "@/lib/api/messages"
import type { Conversation, Message } from "@/lib/api"

type Props = {
  documentId: number
  selectionText: string
}

type FetchState = "idle" | "loading" | "error"

export function AssistantPanel({ documentId, selectionText }: Props) {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [conversationState, setConversationState] = useState<FetchState>("idle")
  const [messages, setMessages] = useState<Message[]>([])
  const [messagesState, setMessagesState] = useState<FetchState>("idle")
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null)
  const [inputValue, setInputValue] = useState("")
  const [isCreating, setIsCreating] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [streamStage, setStreamStage] = useState<string | null>(null)
  const composerRef = useRef<HTMLTextAreaElement | null>(null)

  const loadConversations = useCallback(async () => {
    setConversationState("loading")
    try {
      const items = await fetchDocumentConversations(documentId)
      const sorted = sortConversations(items)
      setConversations(sorted)
      if (sorted.length > 0) {
        setSelectedConversationId((current) => current ?? sorted[0]?.id ?? null)
      } else {
        setSelectedConversationId(null)
        setMessages([])
      }
      setConversationState("idle")
    } catch (error) {
      console.error("Failed to load conversations", error)
      setConversationState("error")
      toast.error("Could not load assistant conversations.")
    }
  }, [documentId])

  const loadMessages = useCallback(
    async (conversationId: number) => {
      setMessagesState("loading")
      try {
        const items = await fetchMessages(conversationId)
        setMessages(items)
        setMessagesState("idle")
      } catch (error) {
        console.error("Failed to load messages", error)
        setMessagesState("error")
      }
    },
    [],
  )

  useEffect(() => {
    void loadConversations()
  }, [loadConversations])

  useEffect(() => {
    if (!selectedConversationId) {
      setMessages([])
      return
    }
    setStreamStage(null)
    void loadMessages(selectedConversationId)
  }, [selectedConversationId, loadMessages])

  useEffect(() => {
    if (!selectedConversationId) return
    const unsubscribe = subscribeToAssistantStream(selectedConversationId, (event: AssistantStreamEvent) => {
      if (event.stage) {
        setStreamStage(event.stage)
      }
      if (event.type === "completed") {
        setStreamStage(null)
        void loadMessages(selectedConversationId)
      }
    })
    return () => {
      unsubscribe()
    }
  }, [selectedConversationId, loadMessages])

  const handleCreateConversation = useCallback(
    async (title?: string) => {
      setIsCreating(true)
      try {
        const created = await createDocumentConversation(documentId, { title })
        setConversations((prev) => sortConversations([created, ...prev]))
        setSelectedConversationId(created.id)
        setMessages([])
        return created
      } catch (error) {
        console.error("Failed to create conversation", error)
        toast.error("Could not start a new conversation.")
        return null
      } finally {
        setIsCreating(false)
      }
    },
    [documentId],
  )

  const handleSend = async () => {
    const trimmed = inputValue.trim()
    if (!trimmed) return

    let activeConversationId = selectedConversationId
    setIsSending(true)
    try {
      if (!activeConversationId) {
        const created = await handleCreateConversation()
        if (!created) return
        activeConversationId = created.id
      }
      await sendMessage(activeConversationId, { content: trimmed, role: "user" })
      setInputValue("")
      composerRef.current?.focus()
      await loadMessages(activeConversationId)
    } catch (error) {
      console.error("Failed to send message", error)
      toast.error("Could not send message. Please try again.")
    } finally {
      setIsSending(false)
    }
  }

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === selectedConversationId) ?? null,
    [conversations, selectedConversationId],
  )

  const stageLabel = streamStage
    ? streamStage === "queued"
      ? "Queued"
      : streamStage === "generating"
        ? "Generating"
        : streamStage
    : null

  const handleSelectionShortcut = () => {
    if (!selectionText) return
    setInputValue((prev) => (prev ? `${prev}\n\n${selectionText}` : selectionText))
    composerRef.current?.focus()
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b px-4 py-3">
        <div className="space-y-0.5">
          <h2 className="text-lg font-semibold leading-tight">Assistant</h2>
          <p className="text-xs text-muted-foreground">Ask questions or refine this document.</p>
        </div>
        <div className="flex items-center gap-2">
          <ConversationHistoryMenu
            conversations={conversations}
            activeId={selectedConversationId}
            onSelect={(id) => setSelectedConversationId(id)}
            onRefresh={() => void loadConversations()}
            isLoading={conversationState === "loading"}
          />
          <Button size="icon" variant="ghost" onClick={() => handleCreateConversation()} disabled={isCreating}>
            {isCreating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            <span className="sr-only">New conversation</span>
          </Button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1 flex-col">
        <ScrollArea className="flex-1 px-4">
          <div className="flex flex-1 flex-col gap-3 py-4">
            {messagesState === "loading" && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading conversation…
              </div>
            )}
            {messagesState === "error" && (
              <div className="rounded-md border border-destructive/40 bg-destructive/5 px-3 py-2 text-sm text-destructive">
                Could not load messages.
              </div>
            )}
            {messagesState === "idle" && messages.length === 0 && (
              <div className="rounded-md border border-dashed bg-muted/40 px-3 py-6 text-center text-sm text-muted-foreground">
                {activeConversation
                  ? "No messages yet. Ask the assistant anything about this doc."
                  : "Start a conversation to chat with the assistant."}
              </div>
            )}
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </div>
        </ScrollArea>

        <footer className="border-t px-4 py-3">
          <div className="space-y-2">
            {stageLabel && (
              <Badge variant="outline" className="text-[11px]">
                {stageLabel === "generating" && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
                {stageLabel}
              </Badge>
            )}
            {!!selectionText && (
              <button
                type="button"
                onClick={handleSelectionShortcut}
                className="flex items-center gap-2 rounded-lg border border-dashed bg-muted/40 px-3 py-2 text-xs text-muted-foreground transition hover:bg-muted/60"
              >
                <MessageSquarePlus className="h-3.5 w-3.5 text-muted-foreground" />
                Use recent selection as context
              </button>
            )}
            <div className="flex flex-col gap-2">
              <textarea
                ref={composerRef}
                value={inputValue}
                onChange={(event) => setInputValue(event.target.value)}
                placeholder={selectedConversationId ? "Ask a question or request a draft…" : "Start a conversation…"}
                className="min-h-[72px] w-full resize-none rounded-xl border bg-white px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-sky-300"
              />
              <div className="flex items-center justify-between">
                <p className="text-xs text-muted-foreground">
                  Responses are mocked for now but follow the final assistant flow.
                </p>
                <Button size="sm" disabled={isSending || !inputValue.trim()} onClick={handleSend}>
                  {isSending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
                  Send
                </Button>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}

function ConversationHistoryMenu({
  conversations,
  activeId,
  onSelect,
  onRefresh,
  isLoading,
}: {
  conversations: Conversation[]
  activeId: number | null
  onSelect: (id: number) => void
  onRefresh: () => void
  isLoading: boolean
}) {
  const activeTitle = conversations.find((c) => c.id === activeId)?.title || (activeId ? "Untitled" : "No conversation")

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="flex items-center gap-2 border-dashed"
          aria-label="Previous conversations"
        >
          <RotateCw className="h-4 w-4" />
          <span className="hidden sm:inline text-xs">{isLoading ? "Loading…" : activeTitle}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-64">
        <DropdownMenuLabel className="flex items-center justify-between text-xs uppercase text-muted-foreground">
          Conversations
          <button
            onClick={onRefresh}
            className="text-[11px] font-medium text-sky-700 hover:underline"
            disabled={isLoading}
          >
            Refresh
          </button>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {conversations.length === 0 && (
          <DropdownMenuItem className="text-xs text-muted-foreground" disabled>
            No conversations yet.
          </DropdownMenuItem>
        )}
        {conversations.map((conversation) => (
          <DropdownMenuItem
            key={conversation.id}
            onSelect={() => onSelect(conversation.id)}
            className={cn(
              "flex items-center justify-between text-sm",
              activeId === conversation.id ? "bg-sky-50 text-sky-900" : "",
            )}
          >
            <span className="truncate">{conversation.title || "Untitled"}</span>
            {activeId === conversation.id && <span className="text-[11px] text-sky-700">Current</span>}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function sortConversations(items: Conversation[]): Conversation[] {
  return [...items].sort((a, b) => {
    const aTime = a.created_at ? new Date(a.created_at).getTime() : 0
    const bTime = b.created_at ? new Date(b.created_at).getTime() : 0
    if (aTime === bTime) return (b.id ?? 0) - (a.id ?? 0)
    return bTime - aTime
  })
}

function MessageBubble({ message }: { message: Message }) {
  const isAssistant = message.role !== "user"
  const timestamp = message.created_at ? new Date(message.created_at) : null
  const formattedTime = timestamp?.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })

  return (
    <div className={cn("flex flex-col gap-1", isAssistant ? "items-start" : "items-end")}>
      <div
        className={cn(
          "max-w-[90%] rounded-2xl border px-3 py-2 text-sm shadow-sm",
          isAssistant ? "border-slate-200 bg-white text-foreground" : "border-sky-600 bg-sky-600 text-white",
        )}
      >
        <p className="whitespace-pre-line">{message.content}</p>
        {message.status && message.status !== "completed" && (
          <p className="mt-1 text-[10px] uppercase tracking-wide opacity-70">{message.status}</p>
        )}
      </div>
      <span className="text-[11px] uppercase tracking-wide text-muted-foreground">{formattedTime}</span>
    </div>
  )
}
