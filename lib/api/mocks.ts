import type { User, Organization } from "./types"
import type { House, HouseSearch } from "./types"


export const mockOrganizationFree: Organization = {
  id: 1,
  name: "Mocked Free Organization",
  subscriptionId: "free",
}

export const mockOrganizationPro: Organization = {
  id: 1,
  name: "Mocked Pro Organization",
  subscriptionId: "pro",
}

export const mockUser: User = {
  id: 1,
  name: "Mocked User",
  email: "test@example.com",
  organization_id: 1,
}


export const mockHouses: House[] = [
  {
    id: 1,
    url: "https://example.com",
    platform: "pararius",
    rawPayload: {},
    priceMonth: 1400,
    city: "Rotterdam",
    cityZone: "Center",
    address: "Example Street 123",
    postalCode: "1234AB",
    lastUpdatedAt: new Date().toISOString(),
  },
]

export const mockHouseSearches: HouseSearch[] = [
  {
    id: 1,
    city: "Rotterdam",
    filters: { max_price: 1500 },
    createdAt: new Date().toISOString(),
  },
]
