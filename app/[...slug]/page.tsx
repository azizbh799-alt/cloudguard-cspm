import { PageContent } from '@/app/page'
import { StoreProvider } from '@/lib/store'
export default function CatchAllPage(){return <StoreProvider><PageContent/></StoreProvider>}
