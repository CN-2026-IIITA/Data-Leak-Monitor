import { withAuth } from "next-auth/middleware";

export default withAuth({
  pages: {
    signIn: "/login",
  },
});

export const config = {
  matcher: ["/((?!login|signup|setup|_next|api/auth|favicon.ico|.*\\..*).*)"],
};
