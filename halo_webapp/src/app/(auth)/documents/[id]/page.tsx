import { notFound } from "next/navigation"
import { DocumentWorkspace } from "./_components/document-workspace"

type Params = {
  params: Promise<{ id: string }>
}

export default async function DocumentRoute({ params }: Params) {
  const { id } = await params
  const documentId = Number(id)
  if (Number.isNaN(documentId)) {
    notFound()
  }

  return (
    <div className="h-full">
      <DocumentWorkspace documentId={documentId} />
    </div>
  )
}
