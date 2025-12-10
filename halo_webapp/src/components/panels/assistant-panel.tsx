"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { ArrowUp, Loader2, MessageSquarePlus, Plus, RotateCw, X } from "lucide-react"
import { toast } from "sonner"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

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
import type { Conversation, Message, MessageContext } from "@/lib/api"

type Props = {
  documentId: number
  selectionText: string
}

type FetchState = "idle" | "loading" | "error"

type AttachedSection = {
  index: number
  content: string
  id?: number
}

type AttachedSource = {
  id: number
  title: string
}

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
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  // Context attachment state
  const [attachedSections, setAttachedSections] = useState<AttachedSection[]>([])
  const [attachedSources, setAttachedSources] = useState<AttachedSource[]>([])
  const [isDragOver, setIsDragOver] = useState(false)

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
      if (event.type === "delta" && event.assistant_message_id && event.content) {
        setMessages((prev) => {
          const index = prev.findIndex((m) => m.id === event.assistant_message_id)
          if (index !== -1) {
            // Update existing message
            const newMessages = [...prev]
            newMessages[index] = {
              ...newMessages[index],
              content: newMessages[index].content + event.content,
            }
            return newMessages
          }
          // If we don't have the message yet (rare race condition if SSE connects before POST returns),
          // we could technically create a placeholder, but simpler to ignore until we have the shell.
          // However, for better UX with optimistic updates, we might want to handle this.
          // For now, let's assume the POST returns the shell quickly enough or we rely on the "completed" event refresh.
          return prev
        })
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

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages])

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

      // Build context object
      const context: MessageContext = {}

      // Add section IDs if attached
      if (attachedSections.length > 0) {
        const ids = attachedSections.map(s => s.id).filter((id): id is number => id !== undefined)
        if (ids.length > 0) {
          context.section_ids = ids
        }
      }

      // Add content IDs if attached
      if (attachedSources.length > 0) {
        const ids = attachedSources.map(s => s.id)
        if (ids.length > 0) {
          context.content_ids = ids
        }
      }

      // Add selection if present
      if (selectionText) {
        context.selection = { text: selectionText }
      }

      // Optimistic user message
      const optimisticUserMessage: Message = {
        id: -1, // Temporary ID
        conversation_id: activeConversationId,
        role: "user",
        content: trimmed,
        created_at: new Date().toISOString(),
        status: "completed",
      }

      // Optimistic assistant placeholder
      const optimisticAssistantMessage: Message = {
        id: -2, // Temporary ID, will be replaced by real one when stream starts or POST returns
        conversation_id: activeConversationId,
        role: "assistant",
        content: "",
        created_at: new Date().toISOString(),
        status: "running",
      }

      setMessages((prev) => [...prev, optimisticUserMessage, optimisticAssistantMessage])
      setInputValue("")
      setAttachedSections([])
      setAttachedSources([])
      composerRef.current?.focus()

      const sentMessage = await sendMessage(activeConversationId, {
        content: trimmed,
        role: "user",
        context_sources: Object.keys(context).length > 0 ? context : undefined,
      })

      // Replace optimistic user message with real one
      // And we rely on loadMessages or stream to update the assistant one.
      // Actually, since sendMessage returns the user message, we can update that.
      // The assistant message is created on the backend. We'll get its ID from the stream events hopefully or next fetch.
      // But wait, `sendMessage` in FE returns `Message`. The backend `create_message` returns `created_user_message`.
      // So we don't get the assistant message ID immediately from the POST response.
      // We need to wait for the stream to give us the ID or reload messages.

      // Let's just reload messages to get the real IDs and the initial empty assistant message.
      await loadMessages(activeConversationId)
    } catch (error) {
      console.error("Failed to send message", error)
      toast.error("Could not send message. Please try again.")
    } finally {
      setIsSending(false)
    }
  }

  // Drag and drop handlers for context attachment
  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault()
    setIsDragOver(false)

    try {
      // Check for section drag
      const sectionData = event.dataTransfer.getData("application/x-section")
      if (sectionData) {
        const section: AttachedSection = JSON.parse(sectionData)
        // Avoid duplicates
        if (!attachedSections.some(s => s.index === section.index)) {
          setAttachedSections(prev => [...prev, section])
          toast.success("Section attached to context")
        }
        return
      }

      // Check for content/source drag
      const contentId = event.dataTransfer.getData("application/x-content-id")
      if (contentId) {
        const id = Number.parseInt(contentId, 10)
        if (!Number.isNaN(id)) {
          // Get title from data transfer if available
          const title = event.dataTransfer.getData("application/x-content-title") || `Source ${id}`

          // Avoid duplicates
          if (!attachedSources.some(s => s.id === id)) {
            setAttachedSources(prev => [...prev, { id, title }])
            toast.success("Source attached to context")
          }
        }
        return
      }
    } catch (error) {
      console.error("Error handling drop:", error)
      toast.error("Could not attach context")
    }
  }

  const removeSection = (index: number) => {
    setAttachedSections(prev => prev.filter(s => s.index !== index))
  }

  const removeSource = (id: number) => {
    setAttachedSources(prev => prev.filter(s => s.id !== id))
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

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      void handleSend()
    }
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex shrink-0 items-center justify-between border-b px-4 py-3">
        <div className="space-y-0.5">
          <h2 className="text-lg font-semibold leading-tight">Assistant</h2>
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

      <div className="flex-1 min-h-0 overflow-hidden">
        <ScrollArea className="h-full px-4">
          <div className="flex flex-col gap-3 py-4">
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
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
      </div>

      <footer
        className={cn(
          "shrink-0 border-t px-4 py-3 transition-colors",
          isDragOver && "bg-sky-50 border-sky-300"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
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

            {/* Context pills */}
            {(attachedSections.length > 0 || attachedSources.length > 0) && (
              <div className="flex flex-wrap gap-1.5 rounded-lg border border-dashed bg-muted/30 p-2">
                {attachedSections.map((section) => {
                  const previewText = section.content.trim() || `Section ${section.index + 1}`
                  const truncated = previewText.length > 40 ? previewText.slice(0, 40) + "..." : previewText
                  return (
                    <Badge
                      key={section.index}
                      variant="secondary"
                      className="flex items-center gap-1 pr-1 text-xs"
                    >
                      <span className="max-w-[160px] truncate" title={section.content}>
                        {truncated}
                      </span>
                      <button
                        type="button"
                        onClick={() => removeSection(section.index)}
                        className="ml-0.5 rounded-sm hover:bg-muted-foreground/20"
                        aria-label="Remove section"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  )
                })}
                {attachedSources.map((source) => (
                  <Badge
                    key={source.id}
                    variant="secondary"
                    className="flex items-center gap-1 pr-1 text-xs"
                  >
                    <span className="max-w-[120px] truncate">{source.title}</span>
                    <button
                      type="button"
                      onClick={() => removeSource(source.id)}
                      className="ml-0.5 rounded-sm hover:bg-muted-foreground/20"
                      aria-label="Remove source"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}

            {isDragOver && (
              <div className="rounded-lg border-2 border-dashed border-sky-400 bg-sky-50/50 px-4 py-3 text-center">
                <p className="text-sm font-medium text-sky-700">Drop to attach as context</p>
              </div>
            )}

            <div className="flex flex-col gap-2">
              <div className="flex items-end gap-2 rounded-xl border bg-white px-2 py-2 shadow-sm focus-within:ring-2 focus-within:ring-sky-200">
                <textarea
                  ref={composerRef}
                  value={inputValue}
                  onChange={(event) => setInputValue(event.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={selectedConversationId ? "Ask a question or request a draft…" : "Start a conversation…"}
                  className="min-h-[64px] w-full resize-none rounded-lg border-0 bg-transparent px-2 py-1 text-sm focus-visible:outline-none"
                />
                <Button
                  size="icon"
                  variant="secondary"
                  className="h-9 w-9 rounded-full bg-sky-600 text-white hover:bg-sky-700 disabled:opacity-50"
                  disabled={isSending || !inputValue.trim()}
                  onClick={handleSend}
                  aria-label="Send message"
                >
                  {isSending ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUp className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          </div>
        </footer>
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
  const isStreaming = message.status && message.status !== "completed" && message.status !== "failed"

  return (
    <div className={cn("flex flex-col gap-1", isAssistant ? "items-start" : "items-end")}>
      <div
        className={cn(
          "max-w-[90%] rounded-2xl border px-3 py-2 text-sm shadow-sm break-words",
          isAssistant ? "border-slate-200 bg-white text-foreground" : "border-sky-600 bg-sky-600 text-white",
        )}
      >
        {isAssistant && isStreaming && !message.content ? (
          <div className="flex items-center gap-1 py-1 px-1">
            <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-sky-500 [animation-delay:-0.3s]" />
            <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-sky-500 [animation-delay:-0.15s]" />
            <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-sky-500" />
          </div>
        ) : isAssistant ? (
          <div className="prose prose-sm max-w-none prose-neutral dark:prose-invert break-words [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content + (isStreaming ? "●" : "")}
            </ReactMarkdown>
          </div>
        ) : (
          <p className="whitespace-pre-line break-words">{message.content}</p>
        )}
      </div>
      <span className="text-[11px] uppercase tracking-wide text-muted-foreground">{formattedTime}</span>
    </div>
  )
}
