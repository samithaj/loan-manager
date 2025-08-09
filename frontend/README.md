This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

Preferred (Makefile):

```bash
make install      # installs BE/FE deps
export DATABASE_URL=postgresql://postgres@localhost:5432/loan_manager
createdb loan_manager 2>/dev/null || true
make db           # apply schema + seed
make dev          # runs BE and FE with hot reload
```

Or run FE only:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Login

Create a user then log in:

```bash
curl -i -X POST http://127.0.0.1:8000/v1/users \
  -H "Content-Type: application/json" \
  -d '{"username":"sam","password":"secret","roles":["user"]}'
```

Visit http://localhost:3000/login and sign in with `sam`.
