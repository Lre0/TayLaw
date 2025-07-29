import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = 'https://4dfad74b8181.ngrok-free.app'

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/')
  const searchParams = request.nextUrl.searchParams.toString()
  const url = `${BACKEND_URL}/${path}${searchParams ? `?${searchParams}` : ''}`

  try {
    const response = await fetch(url, {
      headers: {
        'ngrok-skip-browser-warning': 'true'
      }
    })

    const data = await response.text()
    
    return new NextResponse(data, {
      status: response.status,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': '*',
      },
    })
  } catch (error) {
    return NextResponse.json(
      { error: `Proxy error: ${error}` },
      { status: 500 }
    )
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/')
  const url = `${BACKEND_URL}/${path}`

  try {
    const body = await request.formData()
    
    const response = await fetch(url, {
      method: 'POST',
      body: body,
      headers: {
        'ngrok-skip-browser-warning': 'true'
      }
    })

    const data = await response.text()
    
    return new NextResponse(data, {
      status: response.status,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': '*',
      },
    })
  } catch (error) {
    return NextResponse.json(
      { error: `Proxy error: ${error}` },
      { status: 500 }
    )
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': '*',
    },
  })
}